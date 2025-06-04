import json

import requests
from cdislogging import get_logger

from amanuensis.auth.auth import get_jwt_from_header
from pcdcutils.gen3 import Gen3RequestManager, SignaturePayload
from pcdcutils.errors import NoKeyError
from pcdcutils.helpers import encode_str
from amanuensis.config import config
from amanuensis.errors import InternalError, Unauthorized

logger = get_logger(__name__)


def fence_get_users(usernames=None, ids=None):
    """
    amanuensis sends a request to fence for a list of user ids
    matching the supplied list of user email addresses
    """
    if ids and usernames:
        logger.error(
            "fence_get_users: Wrong params, only one among `ids` and `usernames` should be set."
        )
        return {}

    if usernames:
        queryBody = {"usernames": usernames}
    elif ids:
        queryBody = {"ids": ids}
    else:
        logger.error(
            "fence_get_users: Wrong params, at least one among `ids` and `usernames` should be set."
        )
        return {}

    try:
        url = config["FENCE"] + "/admin/users/selected"
        jwt = get_jwt_from_header()
        headers = {
                "Gen3-Service": config.get("SERVICE_NAME").upper(),
            }
        body = json.dumps(queryBody, separators=(",", ":"))

        if not config.get("RSA_PRIVATE_KEY"):
            logger.error("No RSA_PRIVATE_KEY configured — cannot sign request")
            raise NoKeyError("Missing RSA_PRIVATE_KEY — cannot sign request")

        payload = SignaturePayload(
            method="POST",
            path=url,
            headers=headers,
            body=body
        )

        logger.error("AAAAAAAAA")
        logger.error(payload.get_standardized_payload(config.get("SERVICE_NAME").upper()))

        g3rm = Gen3RequestManager(headers=headers)

        signature = g3rm.make_gen3_signature(payload, config=config)
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = "bearer " + jwt
        headers["Signature"] = "signature " + signature

        logger.error("signature " + signature)

        r = requests.post(url, data=body, headers=headers)
        if r.status_code == 200:
            return r.json()

    except NoKeyError as e:
        logger.error(e)
    except requests.HTTPError as e:
        logger.error(e)

    return {}


def fence_get_all_users():
    """
    amanuensis sends a request to fence for a list of all users
    """
    try:
        url = config["FENCE"] + "/admin/users"
        jwt = get_jwt_from_header()
        headers = {
                "Gen3-Service": config.get("SERVICE_NAME").upper(),
            }

        if not config.get("RSA_PRIVATE_KEY"):
            logger.error("No RSA_PRIVATE_KEY configured — cannot sign request")
            raise NoKeyError("Missing RSA_PRIVATE_KEY — cannot sign request")

        payload = SignaturePayload(
            method="GET",
            path=url,
            headers=headers,
        )

        g3rm = Gen3RequestManager(headers=headers)

        signature = g3rm.make_gen3_signature(payload, config=config)
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = "bearer " + jwt
        headers["Signature"] = "signature " + signature

        r = requests.get(url, headers=headers)

        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401:
            raise InternalError("Fence rejected request for all users from amanuensis")
        else:
            raise InternalError(
                "Fence returned unexpected status code for all users request"
            )

    except Exception as e:
        logger.error(e)
        raise InternalError("Something went wrong when trying to fetch all users")
