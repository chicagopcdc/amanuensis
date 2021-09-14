import flask
import jwt
import smtplib
import json
from cdislogging import get_logger
from gen3authz.client.arborist.errors import ArboristError

from amanuensis.resources import userdatamodel as udm
from amanuensis.resources.userdatamodel import get_all_searches, get_search, get_searches_by_id, create_search, delete_search, update_search
# from amanuensis.auth.auth import get_current_user
# from amanuensis.user import get_current_user

from amanuensis.auth.auth import current_user

from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden
# from amanuensis.jwt.utils import get_jwt_header
# from amanuensis.models import query_for_user
# from amanuensis.auth.auth import register_arborist_user


logger = get_logger(__name__)


def get_all(logged_user_id):
    with flask.current_app.db.session as session:
        return get_all_searches(session, logged_user_id)


def get_by_id(logged_user_id, search_id):
    with flask.current_app.db.session as session:
        search = get_search(session, logged_user_id, search_id)
        return search

def get_by_ids(logged_user_id, search_ids):
    with flask.current_app.db.session as session:
        searches = get_searches_by_id(session, logged_user_id, search_ids)
        return searches



def create(logged_user_id, name, description, filter_object):
    with flask.current_app.db.session as session:    
        return create_search(session, logged_user_id, name, description, filter_object)


def update(logged_user_id, search_id, name, description, filter_object):
    with flask.current_app.db.session as session:
        return update_search(session, logged_user_id, search_id, name, description, filter_object)


def delete(logged_user_id, search_id):
    with flask.current_app.db.session as session:
        return delete_search(session, logged_user_id, search_id)