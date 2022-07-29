import flask
import jwt
import smtplib
import json
from cdislogging import get_logger
from gen3authz.client.arborist.errors import ArboristError
from pcdcutils.environment import is_env_enabled

from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden
from amanuensis.resources import userdatamodel as udm
# from amanuensis.resources.userdatamodel import get_all_messages, get_messages_by_request, send_message
from amanuensis.resources.fence import fence_get_users
from amanuensis.auth.auth import current_user
from amanuensis.models import (
    ConsortiumDataContributor,
    Message,
    Receiver
    # Request
)

# TODO initialize on app init instead of here
from hubspotclient.client.hubspot.client import HubspotClient

logger = get_logger(__name__)


def get_messages(logged_user_id, request_id=None):
    with flask.current_app.db.session as session:
        if request_id:
            msgs = udm.get_messages_by_request(session, logged_user_id, request_id)
        else:
            msgs = udm.get_all_messages(session, logged_user_id)
        
        return msgs


def send_message(logged_user_id, request_id, subject, body):
    with flask.current_app.db.session as session:    

        # Get consortium and check that the request exists
        request = udm.get_request_by_id(session, logged_user_id, request_id)
        # logger.debug("Request: " + str(request))
        consortium_code = request.consortium_data_contributor.code
        # logger.debug(f"Consortium Code: {consortium_code}")
        
        # The hubspot oAuth implementation is on the way, but not supported yet.
        hapikey =  config['HUBSPOT']['API_KEY']
        hubspot = HubspotClient(hubspot_auth_token=hapikey)

        # Get EC members emails
        # returns [ email, disease_group_executive_committee ]
        committee = f"{consortium_code} Executive Committee Member"
        hubspot_response = hubspot.get_contacts_by_committee(committee=committee)
        # logger.debug('Hubspot Response: ' + str(hubspot_response))

        # Connect to fence to get the user.id from the username(email)
        usernames = []
        receivers = []
        if hubspot_response and ('total' in hubspot_response) and int(hubspot_response.get("total", '0')):
            for member in hubspot_response["results"]:
                email = member['properties']['email']
                usernames.append(email)

            # make one request for all users to be messaged
            logger.debug(f"send_message hubspot: {usernames}")
            ec_users_results = fence_get_users(config=config, usernames=usernames)
            logger.debug(f"fence_get_users, ec_users_results: {ec_users_results}")
            ec_users = ec_users_results['users'] if 'users' in ec_users_results else None
            # logger.debug(f"fence_get_users, ec_users: {ec_users}")
           
            if ec_users:
                for ecu in ec_users:
                    # logger.debug(f"send_message to: {ecu}")
                    receivers.append(Receiver(receiver_id=ecu['id']))

        #TODO get requestor email
        # if logged_user_id is commettee memeber send to other commettee members and requestor
        # otherwise send to committee memebers

        return udm.send_message(session, logged_user_id, request_id, subject, body, receivers, usernames)


def send_admin_message(project, consortiums, subject, body):
    # The hubspot oAuth implementation is on the way, but not supported yet.
    hapikey =  config['HUBSPOT']['API_KEY']
    hubspot = HubspotClient(hubspot_auth_token=hapikey)

    receivers = []

    notify_users_id = []
    notify_users_id.append(project.user_id)
    notify_users_id.extend([stat.user_id for stat in project.statisticians if stat.user_id])

    receivers.extend([stat.email for stat in project.statisticians if stat.email and not stat.user_id])

    requesters_obj = fence_get_users(config, ids=notify_users_id)
    requesters = requesters_obj['users'] if 'users' in requesters_obj else None
    logger.info(requesters)
    if requesters:
        requesters_email = [req["name"] for req in requesters]
        receivers.extend(requesters_email)

    for consortium_code in consortiums:
        # Get EC members emails
        # returns [ email, disease_group_executive_committee ]
        committee = f"{consortium_code} Executive Committee Member"
        hubspot_response = hubspot.get_contacts_by_committee(committee=committee)
        # logger.debug('Hubspot Response: ' + str(hubspot_response))
        if hubspot_response and ('total' in hubspot_response) and int(hubspot_response.get("total", '0')):
            for member in hubspot_response["results"]:
                email = member['properties']['email']
                receivers.append(email)

    receivers = list(set(receivers))
    logger.info("Sending email to {}".format(receivers))

    if is_env_enabled("AWS_SES_DEBUG"):
        logger.debug(f"send_message emails (debug mode): {str(receivers)}")
    elif email:
        # Send the Message via AWS SES
        return flask.current_app.boto.send_email_ses(body, receivers, subject)


