import flask
import jwt
import smtplib
import json
from cdislogging import get_logger
from gen3authz.client.arborist.errors import ArboristError

from amanuensis.resources.userdatamodel import (
    create_project,
    get_project_by_consortium,
    get_project_by_user
)
from amanuensis.resources import search, consortium_data_contributor

from amanuensis.auth.auth import current_user


from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden
from amanuensis.utils import get_consortium_list
# from amanuensis.jwt.utils import get_jwt_header
# from amanuensis.models import query_for_user
# from amanuensis.auth.auth import register_arborist_user


from amanuensis.models import (
    Search,
    Request,
    ConsortiumDataContributor,
)


from amanuensis.schema import ProjectSchema



logger = get_logger(__name__)


def get_all(logged_user_id, approver):
    project_schema = ProjectSchema(many=True)
    with flask.current_app.db.session as session:
        if approver:
            #TODO check if the user is part of a EC commettee, if so get the one submitted to the consortium
            #Get consortium
            isEcMember = True
            consortium = "INRG"
            if isEcMember and consortium:
                projects = get_project_by_consortium(session, consortium, logged_user_id)
                project_schema.dump(projects)
                return projects
            else:
                raise NotFound(
                    "User role and consortium not matching or user {} is not assigned to the Executive Commettee in the system. Consortium: {}".format(
                            logged_user_id,
                            consortium
                        )
                    )

        projects = get_project_by_user(session, logged_user_id)
        project_schema.dump(projects)
        return projects


def create(logged_user_id, name, description, search_ids):
    # retrieve all the searches associated with this project
    searches = search.get_by_ids(logged_user_id, search_ids)
    # example searches - [{"id": 4, "user_id": 1, "name": "INRG_1", "description": "", "filter_object": {"race": {"selectedValues": ["Black or African American"]}, "consortium": {"selectedValues": ["INRG"]}, "data_contributor_id": {"selectedValues": ["COG"]}}}]
    
    path = 'http://pcdcanalysistools-service/tools/stats/consortiums'
    consortiums = []
    for s in searches:
        # Get a list of consortiums the cohort of data is from
        # example or retuned values - consoritums = ['INRG']
        # s.filter_object - you can use getattr to get the value or implement __getitem__ - https://stackoverflow.com/questions/11469025/how-to-implement-a-subscriptable-class-in-python-subscriptable-class-not-subsc
        consortiums.extend(get_consortium_list(path, s.filter_object))    


    #TODO make sure to populate the consortium table
    # insert into consortium_data_contributor ("code", "name") values ('INRG','INRG'), ('INSTRUCT', 'INSTRuCT');
    requests = []
    for consortia in consortiums:
        # get consortium's ID
        consortium = consortium_data_contributor.get(code=consortia)
        if consortium is None:
            raise NotFound(
                "Consortium with code {} not found.".format(
                    consortia
                )
            )
        req = Request()
        req.consortium_data_contributor = consortium
        requests.append(req)
  
    with flask.current_app.db.session as session:
        project_schema = ProjectSchema()
        project = create_project(session, logged_user_id, description, searches, requests)
        project_schema.dump(project)
        return project

# def get_by_id(logged_user_id, search_id):
#     with flask.current_app.db.session as session:
#         return get_search(session, logged_user_id, search_id)



# def update(logged_user_id, search_id, name, description, filter_object):
#     with flask.current_app.db.session as session:
#         return update_search(session, logged_user_id, search_id, name, description, filter_object)


# def delete(logged_user_id, search_id):
#     with flask.current_app.db.session as session:
#         return delete_search(session, logged_user_id, search_id)