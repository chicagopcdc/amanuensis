import json
import smtplib
from os import environ

import flask
import jwt
from cdislogging import get_logger
from gen3authz.client.arborist.errors import ArboristError
from userportaldatamodel.consortium_data_contributor import ConsortiumDataContributor

# from amanuensis.resources.consortium_data_contributor import consortium_data_contributor
from amanuensis.config import config
from amanuensis.errors import (
    Forbidden,
    InternalError,
    NotFound,
    Unauthorized,
    UserError,
)
from amanuensis.models import Request, Project, RequestState, State
from amanuensis.resources.userdatamodel.userdatamodel_request import (
    get_request_by_consortium,
    get_request_by_id,
    get_requests,
)
from amanuensis.resources.userdatamodel.userdatamodel_state import (
    get_latest_request_state_by_id
)
from amanuensis.schema import RequestSchema, RequestStateSchema

# from pcdcutils.environment import is_env_enabled

logger = get_logger(__name__)


def get(logged_user_id, consortium=None):
    # TODO
    # Get from hubspot if User is an EC member for this specific consortium or not
    isEcMember = False
    requests = []
    with flask.current_app.db.session as session:
        if consortium and isEcMember:
            requests = get_request_by_consortium(session, logged_user_id, consortium)
        else:
            requests = get_requests(session, logged_user_id)

        request_schema = RequestSchema(many=True)
        request_schema.dump(requests)
        return requests


def get_by_id(logged_user_id, request_id):

    # if is_env_enabled('GEN3_DEBUG') and int(request_id) == 12345:
    #     request = Request()
    #     request.id = 12345
    #     # request.project = Project()
    #     request.create_date = "2021-07-01 12:00:01"
    #     request.update_date = "2021-07-01 12:00:01"
    #     request.consortium_data_contributor_id = 1
    #     consortium = ConsortiumDataContributor(id = 1)
    #     consortium.code = "FAKE"
    #     consortium.name = "FAKE Data Consortium"
    #     consortium.create_date = "2021-07-01 12:00:01"
    #     consortium.update_date = "2021-07-01 12:00:01"
    #     request.consortium_data_contributor = consortium
    #     return request

    with flask.current_app.db.session as session:
        return get_request_by_id(session, logged_user_id, request_id)


def get_latest_request_state(requests=None, request_ids=None):
    with flask.current_app.db.session as session:
        request_state_schema = RequestStateSchema(many=True)
        latest_states = get_latest_request_state_by_id(session, requests=requests, request_ids=request_ids)
        return request_state_schema.dump(latest_states)

        
