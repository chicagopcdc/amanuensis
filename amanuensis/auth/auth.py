from functools import wraps
from flask import current_app, request
from authutils.user import current_user
from cdislogging import get_logger

from cdiserrors import AuthNError
from amanuensis.auth.errors import ArboristError
from amanuensis.errors import Forbidden, Unauthorized

logger = get_logger(__name__)



def get_current_user():
    return current_user

def get_jwt_from_header():
    jwt = None
    auth_header = request.headers.get("Authorization")
    if auth_header:
        items = auth_header.split(" ")
        if len(items) == 2 and items[0].lower() == "bearer":
            jwt = items[1]
    if not jwt:
        raise AuthNError("Didn't receive JWT correctly")
    return jwt

def check_arborist_auth(resource, method, constraints=None):
    """
    Check with arborist to verify the authz for a request.

    Args:
        resource (str):
            Identifier for the thing being accessed. These look like filepaths. This
            ``resource`` must correspond to some resource entered previously in
            arborist. Currently the existing resources are going to be the
            program/projects set up by the user sync.
        method (str):
            Identifier for the action the user is trying to do. Like ``resource``, this
            is something that has to exist in arborist already.
        constraints (Optional[Dict[str, str]]):
            Optional set of constraints to send to arborist for context on this request.
            (These really aren't used at all yet.)

    Return:
        Callable: decorator
    """
    constraints = constraints or {}

    def decorator(f):
        @wraps(f)
        def wrapper(*f_args, **f_kwargs):
            if not hasattr(current_app, "arborist"):
                raise Forbidden(
                    "this amanuensis instance is not configured with arborist;"
                    " this endpoint is unavailable"
                )
            if not current_app.arborist.auth_request(
                jwt=get_jwt_from_header(),
                service="amanuensis",
                methods=method,
                resources=resource,
            ):
                raise Forbidden("user does not have privileges to access this endpoint")
            return f(*f_args, **f_kwargs)

        return wrapper

    return decorator

def has_arborist_access(resource, method):
    """
    Check with arborist to verify the authz for a request.

    Args:
        resource (str):
            Identifier for the thing being accessed. These look like filepaths. This
            ``resource`` must correspond to some resource entered previously in
            arborist. Currently the existing resources are going to be the
            program/projects set up by the user sync.
        method (str):
            Identifier for the action the user is trying to do. Like ``resource``, this
            is something that has to exist in arborist already.

    Return:
        true/false
    """
    if not hasattr(current_app, "arborist"):
        raise Forbidden(
            "this amanuensis instance is not configured with arborist;"
            " this endpoint is unavailable"
        )

    if not current_app.arborist.auth_request(
        jwt=get_jwt_from_header(),
        service="amanuensis",
        methods=method,
        resources=resource,
    ):
        return False
    return True
