import flask
import json
from cdislogging import get_logger

from amanuensis.resources.userdatamodel import (
    create_consortium,
    get_consotium_by_code,
)
from amanuensis.resources import filterset
from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden
from amanuensis.models import (
    ConsortiumDataContributor
)


logger = get_logger(__name__)


def create(logged_user_id, name, code):
    with flask.current_app.db.session as session:
        return create_consortium(session, code=code, name=name)

def get(code,session = None):
    if code is None:
        return None

    if session:
        return get_consotium_by_code(session, code=code)
    else:
        with flask.current_app.db.session as session:
            return get_consotium_by_code(session, code=code)






    

