import flask
import requests

import re

from json import dumps
from amanuensis.config import config
from cdislogging import get_logger

logger = get_logger(__name__)



def request_hubspot(data={}, method="POST", path="/"):
    try:
        url = "https://api.hubapi.com/crm/v3/objects" + path
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        querystring = {"hapikey": flask.current_app.hubspot_api_key}
        return requests.request(method, url, data=dumps(data), headers=headers, params=querystring)
    except Exception as e:
        logger.error(e)


#TODO is this used at all???
def is_domain(name):
    # copied from https://validators.readthedocs.io/en/latest/_modules/validators/domain.html
    pattern = re.compile(
        r'^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
        r'([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
        r'([a-zA-Z0-9][-_.a-zA-Z0-9]{0,61}[a-zA-Z0-9]))\.'
        r'([a-zA-Z]{2,13}|[a-zA-Z0-9-]{2,30}.[a-zA-Z]{2,3})$'
    )
    return pattern.match(name)


def get_users(email, hubspot_id):
    '''
    get one or many users by email
    '''
    emails = []
    filter_groups = []

    if isinstance(email, basestring):
        emails.append(email)
    else:
        # hey hey, it's an array
        emails = email

    for e in emails:
        filter_groups.append({
            "filters": [ 
                {
                    "value": e,
                    "propertyName": "email",
                    "operator": "EQ"
                }
            ]
        })

    data = {
        "filterGroups": filter_groups,
        "properties": ["firstname", "lastname", "institution", "email"]
    }

    # print("GET HUB USER")
    r = request_hubspot(data=data, path="/contacts/search")
    # {"total": 0, "results": []}
    r = r.json()
    if len(r.get("results")) < 1:
    	return None

    # user_properties = r.get("results")[0].get("properties")
    results = r.get("results")
    user_list = []
    for u in results:
        user_properties = u.get("properties")
        user_list.append({
            "id": u.get("id"),
            "firstname": user_properties.get("firstname"),
            "lastname": user_properties.get("lastname"),
            "institution": user_properties.get("institution"),
            "email": user_properties.get("email")
        })

    return user_list

    # return {
    #     "firstname": user_properties.get("firstname"),
    #     "lastname": user_properties.get("lastname"),
    #     "institution": user_properties.get("institution"),
    #     "email": user_properties.get("email")
    # }
    # return flask.jsonify({"user": {
    #     "firstname": user_properties.get("firstname"),
    #     "lastname": user_properties.get("lastname"),
    #     "institution": user_properties.get("institution"),
    # }})

def is_user(email, hubspot_id):
    data = {
        "filterGroups": [{
            "filters": [{
                "value": email,
                "propertyName": "email",
                "operator": "EQ"
            }]
        }],
        "properties": [""]
    }
    r = request_hubspot(data=data, path="/contacts/search")
    registered = r.json().get("total", 0) > 0
    # return flask.jsonify({"registered": registered})
    return registered


def update_user_info(email, user_info):
	#TODO call hubspot API and return id
	hubspot_id = None
	if is_user(email, None):
		hubspot_id = update_user(email, user_info)
	else:
		create_user(email, user_info)
		hubspot_id = 1

	return hubspot_id


def create_user(email, user_info):
    data = {
        "properties": {
            "email": email,
            "firstname": user_info["firstName"],
            "institution": user_info["institution"],
            "lastname": user_info["lastName"],
        }
    }
    print("CREATE HUB USER")
    r = request_hubspot(data=data, path="/contacts")
    print(r)
    print(r.json())
    print(dumps(r))
    success = r.status_code == requests.codes.created
    #TODO thrpw error if not success
    return flask.jsonify({"success": success})


def update_user(email, user_info):
    data_get = {
        "filterGroups": [{
            "filters": [{
                "value": email,
                "propertyName": "email",
                "operator": "EQ"
            }]
        }],
        "properties": [""]
    }
    print("UPDATES HUB USER")
    r_get = request_hubspot(data=data_get, path="/contacts/search")
    print(dumps(r_get))
    user_id = r_get.json().get("results")[0].get("id")

    data_update = {
        "properties": {
            "firstname": user_info["firstName"],
            "institution": user_info["institution"],
            "lastname": user_info["lastName"],
        }
    }
    r_update = request_hubspot(
        data=data_update, method="PATCH", path=f"/contacts/{user_id}")
    success = r_update.status_code == requests.codes.ok
    #TODO thrpw error if not success
    return user_id




