import flask
import jwt
import smtplib
import json
from cdislogging import get_logger

from amanuensis.resources import userdatamodel as udm
from amanuensis.resources.userdatamodel import (
    get_filter_sets,
    create_filter_set,
    delete_filter_set,
    update_filter_set,
    get_filter_sets_by_user_id, 
    create_filter_set_snapshot, 
    get_snapshot_by_token
)

from amanuensis.schema import SearchSchema

from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden


logger = get_logger(__name__)


def get_all(logged_user_id, explorer_id):
    with flask.current_app.db.session as session:
        return get_filter_sets(session, logged_user_id, None, None, explorer_id)

def get_by_id(logged_user_id, filter_set_id, explorer_id):
    with flask.current_app.db.session as session:
        return get_filter_sets(session, logged_user_id, None, filter_set_id, explorer_id)

def get_by_ids(logged_user_id, is_amanuensis_admin, filter_set_ids, explorer_id):
    # filterset_schema = SearchSchema(many=True)
    with flask.current_app.db.session as session:
        return get_filter_sets(session, logged_user_id, is_amanuensis_admin, filter_set_ids, explorer_id)
        # return filterset_schema.dump(get_filter_sets(session, logged_user_id, is_amanuensis_admin, filter_set_ids, explorer_id)) 

# def get_by_name(user_id, name, explorer_id):
#     with flask.current_app.db.session as session:
#         return get_filter_sets_by_name(session, user_id, None, name, explorer_id)

def get_by_user_id(user_id, is_admin):
    if not isinstance(user_id, int):
        user_id = int(user_id)
    with flask.current_app.db.session as session:
        return get_filter_sets_by_user_id(session, user_id, is_admin)

def create(logged_user_id, is_amanuensis_admin, explorer_id, name, description, filter_object, ids_list, graphql_object):
    with flask.current_app.db.session as session:    
        return create_filter_set(session, logged_user_id, is_amanuensis_admin, explorer_id, name, description, filter_object, ids_list, graphql_object)


def update(logged_user_id, filter_set_id, explorer_id, name, description, filter_object, graphql_object):
    with flask.current_app.db.session as session:
        return update_filter_set(session, logged_user_id, filter_set_id, explorer_id, name, description, filter_object, graphql_object)


def delete(logged_user_id, filter_set_id, explorer_id):
    with flask.current_app.db.session as session:
        return delete_filter_set(session, logged_user_id, filter_set_id, explorer_id)


def create_snapshot(logged_user_id, filter_set_id, users_list):
    with flask.current_app.db.session as session:
        return create_filter_set_snapshot(session, logged_user_id, filter_set_id, users_list)

def get_snapshot(logged_user_id, token):
    with flask.current_app.db.session as session:
        return get_snapshot_by_token(session, logged_user_id, token)
