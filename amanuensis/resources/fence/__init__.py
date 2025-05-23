
import json

import requests
from cdislogging import get_logger

from amanuensis.auth.auth import get_jwt_from_header
from pcdcutils.signature import SignatureManager
from pcdcutils.errors import NoKeyError
from pcdcutils.helpers import encode_str
from amanuensis.config import config
from amanuensis.errors import InternalError, Unauthorized

logger = get_logger(__name__)



def fence_get_users(usernames=None, ids=None):
    '''
    amanuensis sends a request to fence for a list of user ids 
    matching the supplied list of user email addresses
    '''
    if (ids and usernames):
        logger.error("fence_get_users: Wrong params, only one among `ids` and `usernames` should be set.")
        return {}


    if usernames:
        queryBody = {
            'usernames': usernames
        }
    elif ids:
        queryBody = {
            'ids': ids
        }
    else:
        logger.error("fence_get_users: Wrong params, at least one among `ids` and `usernames` should be set.")
        return {}

    
    try:
        # sending request to Fence
        url = config['FENCE'] + "/admin/users/selected"  
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(queryBody)
        jwt = get_jwt_from_header()
        sm = SignatureManager(key=config["RSA_PRIVATE_KEY"])
        
        headers['Authorization'] = 'bearer ' + jwt
        headers['Signature'] = b'signature ' + sm.sign(body)
        headers['Gen3-Service'] = encode_str(config.get('SERVICE_NAME'))

        # logger.debug(f"headers: {str(headers)}")
        # logger.debug(f"data: {str(body)}")
        # logger.debug(f"url: {str(url)}")
        # logger.debug(f"fence_get_users url: {url}")
 
        r = requests.post(
            url, data=body, headers=headers
        )
        if r.status_code == 200:
          return r.json()

    except NoKeyError as e:
        logger.error(e.message)
    except requests.HTTPError as e:
        logger.error(e.message)

    return{}

def fence_get_all_users():
    '''
    amanuensis sends a request to fence for a list of all users 
    '''
    
    try:
        # sending request to Fence
        url = config['FENCE'] + "/admin/users"  
        headers = {'Content-Type': 'application/json'}
        body = json.dumps({"dummy": "data"})
        jwt = get_jwt_from_header()
        sm = SignatureManager(key=config["RSA_PRIVATE_KEY"])
        
        headers['Authorization'] = 'bearer ' + jwt
        headers['Signature'] = b'signature ' + sm.sign(body)
        headers['Gen3-Service'] = encode_str(config.get('SERVICE_NAME'))
 
        r = requests.get(
            url, data=body, headers=headers
        )

        if r.status_code == 200:
            return r.json()
        
        elif r.status_code == 401:
            raise InternalError("Fence rejected request for all users from amanuensis")
        
        else: 
            raise InternalError("Fence returned unexpected status code for all users request")

    except Exception as e:
        logger.error(e)
        raise InternalError("Something went wrong when trying to fetch all users")