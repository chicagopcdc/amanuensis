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
        query_body = {"usernames": usernames}
    elif ids:
        query_body = {"ids": ids}
    else:
        logger.error(
            "fence_get_users: Wrong params, at least one among `ids` and `usernames` should be set."
        )
        return {}

    try:
        # Sending request to Fence.
        url = config["FENCE"] + "/admin/users/selected"
        path = "/admin/users/selected"
        method = "POST"
        service_name = config.get("SERVICE_NAME")
        jwt = get_jwt_from_header()

        body = json.dumps(query_body, separators=(",", ":"))

        g3rm = Gen3RequestManager(headers={"Gen3-Service": service_name})
        signature = g3rm.make_gen3_signature(
            SimpleNamespace(method=method, path=path, body=lambda: body.encode()),
            config,
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {jwt}",
            "Signature": b"signature " + signature,
            "Gen3-Service": encode_str(service_name),
        }

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
        # Sending request to Fence.
        url = config["FENCE"] + "/admin/users"
        path = "/admin/users"
        method = "GET"
        service_name = config.get("SERVICE_NAME")
        jwt = get_jwt_from_header()

        g3rm = Gen3RequestManager(headers={"Gen3-Service": service_name})
        signature = g3rm.make_gen3_signature(
            SimpleNamespace(method=method, path=path, body=lambda: ""), config
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {jwt}",
            "Signature": b"signature " + signature,
            "Gen3-Service": encode_str(service_name),
        }

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
