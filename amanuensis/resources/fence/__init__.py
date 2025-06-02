import json

import requests
from cdislogging import get_logger

from amanuensis.auth.auth import get_jwt_from_header
from pcdcutils.gen3 import Gen3RequestManager
from pcdcutils.errors import NoKeyError
from pcdcutils.helpers import encode_str
from amanuensis.config import config
from amanuensis.errors import InternalError, Unauthorized

logger = get_logger(__name__)


class SignaturePayload:
    def __init__(self, method, path, headers=None):
        self.method = method.upper()
        self.path = path
        self.headers = headers or {}

    def get_data(self, as_text=True):
        header_str = "\n".join(f"{k}: {v}" for k, v in sorted(self.headers.items()))
        payload_str = f"{self.method} {self.path}\n{header_str}"
        return payload_str if as_text else payload_str.encode("utf-8")


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

        # --- RSA guard ---
        if not config.get("RSA_PRIVATE_KEY"):
            logger.error("No RSA_PRIVATE_KEY configured — cannot sign request")
            raise NoKeyError("Missing RSA_PRIVATE_KEY — cannot sign request")

        g3rm = Gen3RequestManager(headers={})

        # --- Prepare SignaturePayload ---
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        path_only = parsed_url.path

        payload = SignaturePayload(
            method="POST",
            path=path_only,
            headers={"Gen3-Service": config.get("SERVICE_NAME")},
        )

        signature = g3rm.make_gen3_signature(payload, config=config)

        # --- Headers ---
        headers = {
            "Content-Type": "application/json",
            "Authorization": "bearer " + jwt,
            "Signature": b"signature " + signature,
            "Gen3-Service": encode_str(config.get("SERVICE_NAME")),
        }

        body = json.dumps(queryBody)

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

        # --- RSA guard ---
        if not config.get("RSA_PRIVATE_KEY"):
            logger.error("No RSA_PRIVATE_KEY configured — cannot sign request")
            raise NoKeyError("Missing RSA_PRIVATE_KEY — cannot sign request")

        g3rm = Gen3RequestManager(headers={})

        # --- Prepare SignaturePayload ---
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        path_only = parsed_url.path

        payload = SignaturePayload(
            method="GET",
            path=path_only,
            headers={"Gen3-Service": config.get("SERVICE_NAME")},
        )

        signature = g3rm.make_gen3_signature(payload, config=config)

        # --- Headers ---
        headers = {
            "Content-Type": "application/json",
            "Authorization": "bearer " + jwt,
            "Signature": b"signature " + signature,
            "Gen3-Service": encode_str(config.get("SERVICE_NAME")),
        }

        # --- NOTE: GET request — NO body needed anymore! ---
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
