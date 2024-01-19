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
from amanuensis.resources.request import get_request_state
from amanuensis.resources.userdatamodel.userdatamodel_request import (
    get_requests_by_project_id,
)

from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden
from amanuensis.utils import get_consortium_list
from amanuensis.resources.fence import fence_get_users

from amanuensis.models import (
    Request,
    ConsortiumDataContributor,
    AssociatedUser
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
    filter_sets = filterset.get_by_ids(logged_user_id, is_amanuensis_admin, filter_set_ids, explorer_id)
    # example filter_sets - [{"id": 4, "user_id": 1, "name": "INRG_1", "description": "", "filter_object": {"race": {"selectedValues": ["Black or African American"]}, "consortium": {"selectedValues": ["INRG"]}, "data_contributor_id": {"selectedValues": ["COG"]}}}]

    path = 'http://pcdcanalysistools-service/tools/stats/consortiums'
    consortiums = []
    for s in filter_sets:
        # Get a list of consortiums the cohort of data is from
        # example or retuned values - consoritums = ['INRG']
        # s.filter_object - you can use getattr to get the value or implement __getitem__ - https://stackoverflow.com/questions/11469025/how-to-implement-a-subscriptable-class-in-python-subscriptable-class-not-subsc
        consortiums.extend(get_consortium_list(path, s.graphql_object, s.ids_list))    
    consortiums = list(set(consortiums))

    # Defaulst state is SUBMITTED
    default_state = admin.get_by_code("IN_REVIEW")

    #TODO make sure to populate the consortium table
    # insert into consortium_data_contributor ("code", "name") values ('INRG','INRG'), ('INSTRUCT', 'INSTRuCT');
    requests = []
    for consortia in consortiums:
        # get consortium's ID
        consortium = consortium_data_contributor.get(code=consortia.upper())
        if consortium is None:
            raise NotFound(
                "Consortium with code {} not found.".format(
                    consortia
                )
            )
        req = Request()
        req.consortium_data_contributor = consortium
        req.states.append(default_state)
        requests.append(req)

    # Check if associated_users exists in amanuensis
    # 1. get associated_users from amanuensis
    amanuensis_associated_users = get_all_associated_users(associated_users_emails) 

    # # 1. check if associated_users are already in amanuensis
    # for associated_user in amanuensis_associated_users:
    #     if associated_user.ema
    # registered_stat = 
    # missing_users_email = 

    # # 2. Check if associated_user exists in fence. If so assign user_id, otherwise use the submitted email.
    # fence_users = fence_get_users(config=config, usernames=associated_user_emails)
    # fence_users = fence_users['users'] if 'users' in fence_users else []
    
    # 2. Check if any associated_user is not in the DB yet
    missing_users_email = []
    if len(associated_users_emails) != len(amanuensis_associated_users):
        users_email = [user.email for user in amanuensis_associated_users]
        missing_users_email = [email for email in associated_users_emails if email not in users_email]

    # 3. link the existing statician to the project
    associated_users = []
    for user in amanuensis_associated_users:
        associated_user = user
        associated_users.append(associated_user)

    # 4 or create them if they have not been previously
    for user_email in missing_users_email:
        associated_user = AssociatedUser(email=user_email)
        associated_users.append(associated_user)


    with flask.current_app.db.session as session:
        project_schema = ProjectSchema()
        project = create_project(session, logged_user_id, description, name, institution, filter_sets, requests, associated_users)
        project_schema.dump(project)
        return project


def update(project_id, approved_url, filter_set_ids):
    # TODO retrieve all the filter_sets associated with this project
    # NOT SUPPORTED YET

    if not approved_url:
        return None

    with flask.current_app.db.session as session:
        return update_project(session, project_id, approved_url)


def update_project_request_states(requests, state_code):
    with flask.current_app.db.session as session:
        state = get_state_by_code(session, state_code)
        for request in requests:
            update_request_state(session, request, state)



def update_project_searches(logged_user_id, project_id, filter_sets_id):
    project_schema = ProjectSchema()
    with flask.current_app.db.session as session:
        # Retrieve the project
        project = get_project_by_id(session, logged_user_id, project_id)
        if not project:
            raise NotFound("The project with id {} has not been found".format(project_id))

        # Retrieve all the filter_sets
        filter_sets = filterset.get_filter_sets_by_ids_f(filter_sets_id) 

        # TODO make this a config variable in amanuensis-config.yaml
        path = 'http://pcdcanalysistools-service/tools/stats/consortiums'
        new_consortiums = []
        for s in filter_sets:
            # s.filter_object - you can use getattr to get the value or implement __getitem__ - https://stackoverflow.com/questions/11469025/how-to-implement-a-subscriptable-class-in-python-subscriptable-class-not-subsc
            new_consortiums.extend(get_consortium_list(path, s.graphql_object, s.ids_list))    
        new_consortiums = list(set(new_consortiums))
        new_consortiums = [consortium.upper() for consortium in new_consortiums]
            
        # Get all the consortium involved in the existing requests
        requests = project.requests
        requests_with_state = [{"request": request, "state": get_request_state(request.id, session).state} for request in requests]
        # TODO make this configurable
        old_consortiums = [request["request"].consortium_data_contributor.code for request in requests_with_state if request["state"].code not in ["WITHDRAWAL"]]

        # Check if the consortium list is changed after changing the associated search
        add_consortiums = list(set(new_consortiums) - set(old_consortiums))
        remove_consortiums = list(set(old_consortiums) - set(new_consortiums))

        if add_consortiums and len(add_consortiums) > 0:
            # Defaulst state is SUBMITTED
            default_state = admin.get_by_code("IN_REVIEW")
            if not default_state:
                raise NotFound("The state with id {} has not been found".format(default_state))

            existing_consortiums_ids = [r.consortium_data_contributor_id for r in project.requests]
            existing_consortiums_ids = list(set(existing_consortiums_ids))

            for add_consortium in add_consortiums:
                consortium = consortium_data_contributor.get(code=add_consortium, session=session)
                if consortium is None:
                    raise NotFound(
                        "Consortium with code {} not found.".format(
                            add_consortium
                        )
                    )

                if consortium.id in existing_consortiums_ids:
                    # Update existing request record
                    for r in project.requests:
                        if r.consortium_data_contributor_id == consortium.id:
                            update_request_state(session, r, default_state)
                else:
                    # create a new request record for this consortium
                    req = Request()
                    req.consortium_data_contributor = consortium
                    req.states.append(default_state)
                    project.requests.append(req)


        if remove_consortiums and len(remove_consortiums) > 0:
            default_state = admin.get_by_code("WITHDRAWAL", session)
            if not default_state:
                raise NotFound("The state with id {} has not been found".format(default_state))

            for remove_consortium in remove_consortiums:
                requests_by_project = get_requests_by_project_id(session, project_id)
                for request_by_project in requests_by_project:
                    if request_by_project.consortium_data_contributor.code == remove_consortium:
                        update_request_state(session, request_by_project, default_state)


        # Update he filterset
        # session.query().filter(Institution.uid == uid).update({Institution.display_name: display_name})
        # userdatamodel project -> update_project
        project.searches = filter_sets

        session.commit()
        project_schema.dump(project)
        return project

    


