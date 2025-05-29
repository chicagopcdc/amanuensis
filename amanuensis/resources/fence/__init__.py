import json

import requests
from cdislogging import get_logger

from amanuensis.auth.auth import get_jwt_from_header
from pcdcutils.errors import NoKeyError
from pcdcutils.helpers import encode_str
from pcdcutils.gen3 import Gen3RequestManager
from amanuensis.config import config
from amanuensis.errors import InternalError, Unauthorized
from types import SimpleNamespace

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
        service_name = config.get("SERVICE_NAME", "").upper()

        key = config.get(f"{service_name}_PRIVATE_KEY")

        # Try to find the specific private key for this service (e.g., AMANUENSIS_PRIVATE_KEY).
        # If it's not found, fall back to a shared RSA_PRIVATE_KEY. This supports legacy behavior.
        if not key:
            logger.warning(
                f"{service_name}_PRIVATE_KEY not found. Falling back to RSA_PRIVATE_KEY."
            )
            key = config.get("RSA_PRIVATE_KEY")

        if not key:
            raise NoKeyError(
                f"No signing key found for service {service_name} or fallback RSA_PRIVATE_KEY."
            )

        jwt = get_jwt_from_header()

        body = json.dumps(query_body, separators=(",", ":"))

        # Make a copy of the config and plug in the private key we found
        signing_config = config.copy()
        signing_config[f"{service_name}_PRIVATE_KEY"] = key

        g3rm = Gen3RequestManager(headers={"Gen3-Service": service_name})
        signature = g3rm.make_gen3_signature(
            # Prepare a namespace object containing method, path, and encoded body — this will be signed.
            SimpleNamespace(
                method=method,
                url=SimpleNamespace(path=path),
                body=lambda: body.encode(),
            ),
            signing_config,
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {jwt}",
            "Signature": "signature "
            + (signature.decode() if isinstance(signature, bytes) else signature),
            "Gen3-Service": encode_str(service_name or ""),
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
        service_name = config.get("SERVICE_NAME", "").upper()

        key = config.get(f"{service_name}_PRIVATE_KEY")

        # Try to find the specific private key for this service (e.g., AMANUENSIS_PRIVATE_KEY).
        # If it's not found, fall back to a shared RSA_PRIVATE_KEY. This supports legacy behavior.
        if not key:
            logger.warning(
                f"{service_name}_PRIVATE_KEY not found. Falling back to RSA_PRIVATE_KEY."
            )
            key = config.get("RSA_PRIVATE_KEY")

        if not key:
            raise NoKeyError(
                f"No signing key found for service {service_name} or fallback RSA_PRIVATE_KEY."
            )

        jwt = get_jwt_from_header()

        # Empty body for GET request, but still needs to be encoded for signature
        body = ""

        # Make a copy of the config and plug in the private key we found
        signing_config = config.copy()
        signing_config[f"{service_name}_PRIVATE_KEY"] = key

        g3rm = Gen3RequestManager(headers={"Gen3-Service": service_name})
        signature = g3rm.make_gen3_signature(
            # Prepare a namespace object containing method, path, and encoded body — this will be signed.
            SimpleNamespace(
                method=method,
                url=SimpleNamespace(path=path),
                body=lambda: body.encode(),
            ),
            signing_config,
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {jwt}",
            "Signature": "signature "
            + (signature.decode() if isinstance(signature, bytes) else signature),
            "Gen3-Service": encode_str(service_name or ""),
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

    except NoKeyError as e:
        logger.error(e)
        raise InternalError("No signing key available for Gen3 request")
    except requests.HTTPError as e:
        logger.error(e)
        raise InternalError("HTTP error during request to Fence")
    except Exception as e:
        logger.error(e)
        raise InternalError("Something went wrong when trying to fetch all users")
