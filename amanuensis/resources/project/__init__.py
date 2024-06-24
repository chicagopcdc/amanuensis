import flask
import jwt
import smtplib
import json
from cdislogging import get_logger
from gen3authz.client.arborist.errors import ArboristError

from amanuensis.resources.userdatamodel import (
    create_project,
    get_all_projects,
    get_project_by_consortium,
    get_project_by_user,
    get_project_by_id,
    update_project,
    associate_user,
    update_request_state,
    get_state_by_code
)
from amanuensis.resources import filterset, consortium_data_contributor, admin
from amanuensis.resources.userdatamodel.userdatamodel_request import (
    get_requests_by_project_id,
)
from amanuensis.resources.userdatamodel.userdatamodel_state import get_latest_request_state_by_id
from amanuensis.resources.consortium_data_contributor import get_consortiums_from_fitersets
from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden
from amanuensis.resources.fence import fence_get_users

from amanuensis.models import (
    Request,
    ConsortiumDataContributor,
    AssociatedUser,
    RequestState
)

from amanuensis.schema import ProjectSchema



logger = get_logger(__name__)


def get_all(logged_user_id, logged_user_email, special_user):
    project_schema = ProjectSchema(many=True)
    with flask.current_app.db.session as session:
        if special_user:
            if special_user == "admin":
                projects = get_all_projects(session)
                project_schema.dump(projects)
                return projects

            # #TODO check if the user is part of a EC commettee, if so get the one submitted to the consortium
            # #Get consortium
            # isEcMember = True
            # consortium = "INRG"
            # if isEcMember and consortium:
            #     projects = get_project_by_consortium(session, consortium, logged_user_id)
            #     project_schema.dump(projects)
            #     return projects
            # else:
            #     raise NotFound(
            #         "User role and consortium not matching or user {} is not assigned to the Executive Commettee in the system. Consortium: {}".format(
            #                 logged_user_id,
            #                 consortium
            #             )
            #         )

        projects = get_project_by_user(session, logged_user_id, logged_user_email)
        project_schema.dump(projects)
        return projects


def get_by_id(logged_user_id, project_id):
    project_schema = ProjectSchema()
    with flask.current_app.db.session as session:
        project = get_project_by_id(session, logged_user_id, project_id)
        project_schema.dump(project)
        return project

def get_all_associated_users(emails):
    with flask.current_app.db.session as session:
        associated_users = associate_user.get_associated_users(session, emails)
        return associated_users


def create(logged_user_id, is_amanuensis_admin, name, description, filter_set_ids, explorer_id, institution, associated_users_emails):
    # retrieve all the filter_sets associated with this project
    if is_amanuensis_admin:
        filter_sets = filterset.get_filter_sets_by_ids_f(filter_set_ids) 
    else:
        filter_sets = filterset.get_by_ids(logged_user_id, is_amanuensis_admin, filter_set_ids, explorer_id)
    
    # example filter_sets - [{"id": 4, "user_id": 1, "name": "INRG_1", "description": "", "filter_object": {"race": {"selectedValues": ["Black or African American"]}, "consortium": {"selectedValues": ["INRG"]}, "data_contributor_id": {"selectedValues": ["COG"]}}}]

    consortiums = get_consortiums_from_fitersets(filter_sets)

    # Defaulst state is SUBMITTED
    default_state = admin.get_by_code("IN_REVIEW")


    requests = []
    for consortia in consortiums.values():
        req = Request()
        req.consortium_data_contributor = consortia
        req.states.append(default_state)
        requests.append(req)


    with flask.current_app.db.session as session:
        project_schema = ProjectSchema()
        project = create_project(session, logged_user_id, description, name, institution, filter_sets, requests)
        associated_users = []
        for email in associated_users_emails:
            associated_users.append({"project_id": project.id, "email": email})
        associated_users.append({"project_id": project.id, "id": logged_user_id})
        admin.add_associated_users(associated_users)
        project_schema.dump(project)
        return project


def update(project_id, approved_url, filter_set_ids):
    # TODO retrieve all the filter_sets associated with this project
    # NOT SUPPORTED YET

    if not approved_url:
        return None

    with flask.current_app.db.session as session:
        return update_project(session, project_id, approved_url)


def upload_file(bucket, key, project_id, expires=None):
    try:
        presigned_url = flask.current_app.boto.presigned_url(bucket, key, expires, {}, method="put_object")

    except Exception as e:
        logger.error(f"Failed to generate presigned url: {e}")
        raise InternalError("Failed to generate presigned url")
    
    update(project_id, f"https://{bucket}.s3.amazonaws.com/{key}", None)

    return presigned_url





def update_project_searches(logged_user_id, project_id, filter_sets_id):
    project_schema = ProjectSchema()
    with flask.current_app.db.session as session:
        # Retrieve the project
        project = get_project_by_id(session, logged_user_id, project_id)
        if not project:
            raise NotFound("The project with id {} has not been found".format(project_id))

        # Retrieve all the filter_sets
        filter_sets_id = [filter_sets_id] if not isinstance(filter_sets_id, list) else filter_sets_id
        filter_sets = filterset.get_filter_sets_by_ids_f(filter_sets_id)
        not_found_filter_set_ids = set(filter_sets_id) - set(filter_set.id for filter_set in filter_sets)
        if not_found_filter_set_ids:
            raise NotFound(f"filter-set-id(s), {not_found_filter_set_ids} do not exist")
        

        #remove any filter-sets currently part of proejects
        current_filter_sets = {search.id for search in project.searches}
        filter_sets = [search for search in filter_sets if search.id not in current_filter_sets]
        if not filter_sets:
            logger.info("You must choose a filter-set that is not already part of the project")
            project_schema.dump(project)
            return project

        new_consortiums = get_consortiums_from_fitersets(filter_sets)
        # Get all the consortium involved in the existing requests
        old_consortiums = {request.consortium_data_contributor.code: request for request in project.requests}
        # Check if the consortium list is changed after changing the associated search
        remove_consortiums = old_consortiums.keys() - new_consortiums.keys()
        # Defaulst state is SUBMITTED 
        if new_consortiums:
            IN_REVIEW = admin.get_by_code("IN_REVIEW", session)
            if not IN_REVIEW:
                raise NotFound("The state with code IN_REVIEW has not been found")
            
            for new_consortium_code in new_consortiums:
                if new_consortium_code in old_consortiums:
                    req = old_consortiums[new_consortium_code]
                    req_state = get_latest_request_state_by_id(session, request_ids=req.id)
                    if req_state and req_state[0].state.code == "IN_REVIEW":
                        continue
                else:
                    req = Request()
                    req.consortium_data_contributor = new_consortiums[new_consortium_code]
                    project.requests.append(req)
                update_request_state(session, request=req, state=IN_REVIEW)
        if remove_consortiums:
            DEPRECATED = admin.get_by_code("DEPRECATED", session)
            if not DEPRECATED:
                raise NotFound("The state with code DEPRECATED has not been found")

            for remove_consortium_code in remove_consortiums:
                req = old_consortiums[remove_consortium_code]
                if get_latest_request_state_by_id(session, request_ids=req.id):
                    update_request_state(session, request=req, state=DEPRECATED)


        # Update he filterset
        # session.query().filter(Institution.uid == uid).update({Institution.display_name: display_name})
        # userdatamodel project -> update_project
        project.searches = filter_sets

        session.commit()
        project_schema.dump(project)
        return project

    


