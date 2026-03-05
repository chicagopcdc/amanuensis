import requests, json
from amanuensis.config import config
from cdislogging import get_logger
from amanuensis.errors import InternalError, APIError

logger = get_logger(__name__)

def get_background(name, fuzzy_name):
    """
    Makes a call to the Consolidated Screening List api of developer.trade.gov. Information returned in the dictionary
    can be accessed by info_dict["results"], which is a list of dictionaries containing information about the legality
    of interacting with the returned companies.
    """
    api_url = config["CSL_API"]
    try:
        url = api_url + name + (f"&fuzzy_name={fuzzy_name}" if fuzzy_name else "")
        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'subscription-key': config["CSL_KEY"],
        }

        response = requests.get(url, headers=hdr)

        code = response.status_code
        r = response.text
        info_dict = {}
        if(code == 200):
            info_dict = json.loads(r)
        else:
            logger.error(f"Request unsuccessful: error {code}")
            raise APIError("Request to CSL API failed")
        return info_dict
    except Exception as e:
        logger.error(f"Error in get_background: {e}")
        raise InternalError("Failed to get background information")

