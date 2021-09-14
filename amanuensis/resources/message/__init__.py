import flask
import jwt
import smtplib
import json
from cdislogging import get_logger
from gen3authz.client.arborist.errors import ArboristError

from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden
from amanuensis.resources import userdatamodel as udm
# from amanuensis.resources.userdatamodel import get_all_messages, get_messages_by_request, send_message
from amanuensis.resources.request import get_by_id
from amanuensis.auth.auth import current_user
from amanuensis.models import (
    ConsortiumDataContributor,
    Message,
    Receiver,
    # Request,
    query_for_user
)
# from userdatamodel.user import User
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
        request = get_by_id(logged_user_id, request_id)
        # logger.info("Request: " + str(request))
        consortium_code = request.consortium_data_contributor.code
        logger.info(f"Consortium Code: {consortium_code}")

        
        # The hubspot oAuth implementation is on the way, but not supported yet.
        hubspot_auth_token =  config['HUBSPOT']['API_KEY']
        hubspot = HubspotClient(hubspot_auth_token)

        # Get EC members emails
        # returns [ email, disease_group_executive_committee ]
        hubspot_response = hubspot.get_contacts_by_committee(f"{consortium_code} Executive Committee Member")

        # logger.info('Hubspot Response: ' + str(hubspot_response))

        emails = []
        receivers = []
        if hubspot_response and int(hubspot_response["total"]):
            for member in hubspot_response["results"]:
                email = member['properties']['email']
                emails.append(email)
                ec_user = query_for_user(session, email)
                if ec_user and ec_user.id:
                    receivers.append(Receiver(receiver_id=ec_user.id))

        #TODO get requestor email
        # if logged_user_id is commettee memeber send to other commettee members and requestor
        # otherwise send to committee memebers

        return udm.send_message(session, logged_user_id, request_id, subject, body, receivers, emails)


