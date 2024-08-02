import flask
import jwt
import smtplib
import json
from cdislogging import get_logger
from gen3authz.client.arborist.errors import ArboristError
from pcdcutils.environment import is_env_enabled

from amanuensis.config import config
from amanuensis.errors import (
    NotFound,
    Unauthorized,
    UserError,
    InternalError,
    Forbidden,
)
from amanuensis.resources import userdatamodel as udm

# from amanuensis.resources.userdatamodel import get_all_messages, get_messages_by_request, send_message
from amanuensis.resources.fence import fence_get_users
from amanuensis.auth.auth import current_user
from flask import current_app
from amanuensis.models import (
    ConsortiumDataContributor,
    Message,
    Receiver,
    # Request
)
from hubspot.crm.contacts import PublicObjectSearchRequest, ApiException


logger = get_logger(__name__)


def get_contacts_by_committee(committee, desired_properties=["email"]):
    """Return desired_properties from contacts as JSON.
    :param committee: str - the name of the committee to search.
    :param desired_properties: list[str] - a list contained the properties that should be returned.
    :return: a JSON str with the results from the search by committee with the filtered properties.
    """

    public_object_search_request = PublicObjectSearchRequest(
        filter_groups=[
            {
                "filters": [
                    {
                        "value": committee,
                        "propertyName": "disease_group_executive_committee",
                        "operator": "EQ",
                    }
                ]
            }
        ],
        properties=["email", "disease_group_executive_committee"],
    )

    try:
        api_response = current_app.hubspot_client.crm.contacts.search_api.do_search(
            public_object_search_request=public_object_search_request
        )

    except ApiException as e:
        print("Exception when calling search_api->do_search: %s\n" % e)

    payload = [result.properties for result in api_response.results]

    return [
        {key: val for key, val in property.items() if key in desired_properties}
        for property in payload
    ]


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

        # Get EC members emails
        # returns [ email, disease_group_executive_committee ]
        committee = f"{consortium_code} Executive Committee Member"
        hubspot_response = get_contacts_by_committee(committee=committee)
        # logger.debug('Hubspot Response: ' + str(hubspot_response))

        # Connect to fence to get the user.id from the username(email)
        usernames = []
        receivers = []
        if hubspot_response:
            for member in hubspot_response:
                usernames.append(member["email"])

            # make one request for all users to be messaged
            logger.debug(f"send_message hubspot: {usernames}")
            ec_users_results = fence_get_users(config=config, usernames=usernames)
            logger.debug(f"fence_get_users, ec_users_results: {ec_users_results}")
            ec_users = (
                ec_users_results["users"] if "users" in ec_users_results else None
            )
            # logger.debug(f"fence_get_users, ec_users: {ec_users}")

            if ec_users:
                for ecu in ec_users:
                    # logger.debug(f"send_message to: {ecu}")
                    receivers.append(Receiver(receiver_id=ecu["id"]))

        # TODO get requestor email
        # if logged_user_id is commettee memeber send to other commettee members and requestor
        # otherwise send to committee memebers

        return udm.send_message(
            session, logged_user_id, request_id, subject, body, receivers, usernames
        )


def send_admin_message(project, consortiums, subject, body):

    if current_app.hubspot_client is None:
        logger.info("missing Hubspot API Key, skipping sending emails update.")
    else:

        receivers = []
        requesters = []
        sender = config["AWS_SES"]["SENDER"]

        notify_users_id = []
        # project request owner
        notify_users_id.append(project.user_id)
        # TODO users asssociate with the project request, it could be email or ID they are not both there
        # TODO update user_id with emails and emails from user_Id with cron side job or at trigger
        # notify_users_id.extend([a_user.user_id for a_user in project.associated_users if a_user.user_id])
        # receivers.extend([stat.email for stat in project.statisticians if stat.email and not stat.user_id])

        requesters_obj = fence_get_users(config, ids=notify_users_id)
        requesters_list = requesters_obj["users"] if "users" in requesters_obj else None
        logger.info(requesters_list)
        if requesters_list:
            requesters = [req["name"] for req in requesters_list]

        # get approver from EC members
        for consortium_code in consortiums:
            # Get EC members emails
            # returns [ email, disease_group_executive_committee ]
            committee = f"{consortium_code} Executive Committee Member"
            hubspot_response = get_contacts_by_committee(committee=committee)
            # logger.debug('Hubspot Response: ' + str(hubspot_response))
            if hubspot_response:
                for member in hubspot_response:
                    receivers.append(member["email"])

        receivers = list(set(receivers))
        requesters = list(set(requesters))
        logger.info(f"Receivers: {receivers}")
        print(f"Receivers {receivers}")
        logger.info("Sending email to {} and {}".format(receivers, requesters))

        if is_env_enabled("AWS_SES_DEBUG"):
            logger.debug(f"send_message emails (debug mode): {str(receivers)}")
            logger.debug(f"send_message emails (debug mode): {str(requesters)}")
            return

        ses_config = {
            "aws_access_key_id": config["AWS_SES"]["AWS_ACCESS_KEY"],
            "aws_secret_access_key": config["AWS_SES"]["AWS_SECRET_KEY"],
            "region_name": config["AWS_SES"]["AWS_REGION"],
        }
        if receivers:
            # Send the Message via AWS SES
            flask.current_app.boto.send_email(
                sender, receivers, subject, body, config=ses_config
            )
        if requesters:
            flask.current_app.boto.send_email(
                sender, requesters, subject, body, config=ses_config
            )
