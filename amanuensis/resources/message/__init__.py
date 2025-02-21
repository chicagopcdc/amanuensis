import flask
from cdislogging import get_logger

from amanuensis.errors import InternalError
from amanuensis.config import config
from amanuensis.resources.userdatamodel.request import get_requests
from amanuensis.resources.userdatamodel.receivers import create_receiver
from amanuensis.resources.userdatamodel.message import get_messages, create_message
from amanuensis.resources.fence import fence_get_users
import flask
from amanuensis.models import (
    Receiver,
    Message
)
from amanuensis.resources.userdatamodel.project import get_projects
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
                        "propertyName": "disease_group_executive_committee", # TODO this might be committee membership and/or disease group affiliationin hubspot
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

def send_message(session, logged_user_id, request_id, subject, body):  

    # Get consortium and check that the request exists
    request = get_requests(session, user_id=logged_user_id, id=request_id)
    # logger.debug("Request: " + str(request))
    consortium_code = request.consortium_data_contributor.code
    # logger.debug(f"Consortium Code: {consortium_code}")
    
    # The hubspot oAuth implementation is on the way, but not supported yet.
    hapikey =  config['HUBSPOT']['ACCESS_TOKEN']
    hubspot = current_app.hubspot_client(hubspot_auth_token=hapikey)

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

    """store message in db and send message to emails via aws ses"""
    new_message = create_message(session, sender_id=logged_user_id, request_id=request_id, body=body)
    if receivers:
        new_message.receivers.extend(receivers)

    if receivers:
        session.add(new_message)
        session.flush()

    elif usernames:
        # Send the Message via AWS SES
        return current_app.ses_boto.send_email_ses(body, usernames, subject)

    return new_message


def send_email(subject, body_text, recipients=None):
    if not flask.current_app.ses_boto:
        logger.warning("SES not configured not sending email")
    
    elif "SENDER" not in config["AWS_CREDENTIALS"]["AWS_SES"]:
        logger.warning("no sender email was provided not provided not sending email")
    
    else:
        flask.current_app.ses_boto.send_email(
            SENDER=config["AWS_CREDENTIALS"]["AWS_SES"]["SENDER"],
            CC_RECIPIENTS=config["AWS_CREDENTIALS"]["AWS_SES"]["CC_RECIPIENTS"],
            RECIPIENT=recipients,
            SUBJECT=subject,
            BODY_HTML=body_text,
        )
