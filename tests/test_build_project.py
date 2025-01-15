import pytest
from mock import patch
from cdislogging import get_logger
from amanuensis.models import *
from amanuensis.schema import *
from datetime import datetime, timedelta
import time
from amanuensis.blueprints.filterset import UserError
import requests
import json 
from amanuensis.config import config



logger = get_logger(logger_name=__name__)

@pytest.fixture(scope="session", autouse=True)
def admin_account(session, register_user):
    user_id, user_email = register_user(email=f"admin@uchicago.edu", name="admin", role="admin")
    admin = AssociatedUser(user_id=user_id, email='admin@uchicago.edu')
    session.add(admin)
    session.commit()
    yield user_id

def test_add_consortium(session, client, admin_account):
    json = {"name": "ENDPOINT_TEST", "code": "ENDPOINT_TEST"}
    response = client.post("/admin/consortiums", json=json, headers={"Authorization": f'bearer {admin_account}'} )
    assert response.status_code == 200
    assert session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "ENDPOINT_TEST").first().id == response.json["id"]
    session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "ENDPOINT_TEST").delete()
    session.commit()


def test_add_state(session, client, admin_account):
    json = {"name": "ENDPOINT_TEST", "code": "ENDPOINT_TEST"}
    response = client.post("/admin/states", json=json, headers={"Authorization": f'bearer {admin_account}'} )
    assert response.status_code == 200
    assert session.query(State).filter(State.code == "ENDPOINT_TEST").first().id == response.json["id"]

    #Test add duplicate state
    json = {"name": "ENDPOINT_TEST", "code": "ENDPOINT_TEST"}
    response = client.post("/admin/states", json=json, headers={"Authorization": f'bearer {admin_account}'} )
    assert response.status_code == 200

    session.query(State).filter(State.code == "ENDPOINT_TEST").delete()
    session.commit()


def test_get_states(client, admin_account):
    response = client.get("/admin/states", headers={"Authorization": f'bearer {admin_account}'} )
    assert 'DEPRECATED' not in [state['code'] for state in response.json]


def test_fence_requests(admin_account, mock_requests_post):
    mock_requests_post()
    from amanuensis.resources.fence import fence_get_users
    response = fence_get_users(ids=[admin_account])
    assert response['users'][0]['id'] == admin_account
    response = fence_get_users(usernames=["admin@uchicago.edu"])
    assert response['users'][0]['id'] == admin_account
    response = fence_get_users(usernames=["doesnotexist@test.com"])
    assert len(response['users']) == 0
    response = fence_get_users(usernames=[None])
    assert len(response['users']) == 0



@pytest.fixture(scope="session")
def project_data(admin_account):
    return {"admin_email": "admin@uchicago.edu", "admin_id": admin_account}
    
@pytest.mark.order(1)
def test_filter_set_user(session, client, register_user, login, project_data):
    user_id, user_email = register_user(f"user_1@{__name__}.com", {__name__})
    
    project_data["user_id"] = user_id
    project_data["user_email"] = user_email

    login(user_id, user_email)
    
    filter_set_create_json = {
                "name":"test_filter_set",
                "description":"",
                "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INSTRuCT", "INRG"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
                "gqlFilter":{"AND":[{"IN":{"consortium":["INSTRuCT", "INRG"]}},{"IN":{"sex":["Male"]}}]}
            }
    filter_set_create_response = client.post(f'/filter-sets?explorerId=1', json=filter_set_create_json, headers={"Authorization": f'bearer {user_id}'})
    assert filter_set_create_response.status_code == 200
    project_data["filter_set_id"] = filter_set_create_response.json['id']

    filter_set_get_response = client.get(f'/filter-sets?explorerId=1', headers={"Authorization": f'bearer {user_id}'})
    assert filter_set_get_response.status_code == 200


    assert project_data["filter_set_id"] == filter_set_get_response.json["filter_sets"][0]["id"]

    """
    user_1 creates a snapshot of the filterset to share with user_2
    """

    filter_set_snapshot_json = {
        "filterSetId": project_data["filter_set_id"]
    }
    snapshot_response = client.post("/filter-sets/snapshot", json=filter_set_snapshot_json, headers={"Authorization": f'bearer {user_id}'})
    assert snapshot_response.status_code == 200

    user_2_id, user_2_email = register_user(f"user_2@{__name__}.com", {__name__})
    project_data["user_2_id"] = user_2_id
    project_data["user_2_email"] = user_2_email

    login(user_2_id, user_2_email)

    get_snapshot_response = client.get(f"/filter-sets/snapshot/{snapshot_response.json}", headers={"Authorization": f'bearer {user_2_id}'})
    assert get_snapshot_response.status_code == 200

    login(user_id, user_email)

    filter_set_change_json = {
            "description":"",
            "ids":None,
            "name":"test_filter_set",
            "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","isExclusion":False,"selectedValues":["INSTRuCT", "INRG"]},"sex":{"__type":"OPTION","isExclusion":False,"selectedValues":["Male","Female"]}}},
            "gqlFilter":{"AND":[{"IN":{"consortium":["INSTRuCT", "INRG"]}},{"IN":{"sex":["Male","Female"]}}]}
        }
    filter_set_create_response = client.put(f'/filter-sets/{project_data["filter_set_id"]}?explorerId=1', json=filter_set_change_json, headers={"Authorization": f'bearer {user_id}'})
    assert filter_set_create_response.status_code == 200

    admin_create_filter_set_json = {
        "user_id": project_data["admin_id"],
        "name":"test_filter_set_correction",
        "description":"",
        "filters":{"AND":[{"IN":{"consortium":["INSTRuCT", "INRG", "MAGIC"]}}]}
    }
    admin_create_filter_set_response = client.post("/admin/filter-sets", json=admin_create_filter_set_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_create_filter_set_response.status_code == 200

    admin_filterset_id = admin_create_filter_set_response.json["id"]
    project_data["admin_filterset_id"] = admin_filterset_id

    admin_copy_search_to_user_json = {
        "filtersetId": admin_filterset_id,
        "userId": project_data["user_id"]
    }
    
    admin_copy_search_to_user_response = client.post("admin/copy-search-to-user", json=admin_copy_search_to_user_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    admin_copy_search_to_user_response.status_code == 200

    #TEST deleting a filter set and readding it
    #Test 

@pytest.mark.order(2)
def test_admin_create_project(session, client, login, project_data, mock_requests_post):



    login(project_data["admin_id"], project_data["admin_email"])
    admin_get_filter_sets_json = {"user_id": project_data["user_id"]}
    admin_get_filter_sets = client.get("/admin/filter-sets/user", json=admin_get_filter_sets_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_get_filter_sets.status_code == 200
    assert project_data["filter_set_id"] == admin_get_filter_sets.json["filter_sets"][0]["id"]

    mock_requests_post(consortiums=["INSTRUCT", "INRG"])

    create_project_json = {
            "user_id": project_data["user_id"],
            "name": f"{__name__}_project",
            "description": "This is an endpoint test project",
            "institution": "test university",
            "filter_set_ids": [project_data["filter_set_id"]],
            "associated_users_emails": []
        }
    create_project_response = client.post('/admin/projects', json=create_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert create_project_response.status_code == 200
    project_id = create_project_response.json['id']
    project_data["project_id"] = project_id

    #test add project owner to associted user and add by user_id
    user_1 = session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_id).join(AssociatedUser, ProjectAssociatedUser.associated_user).filter(AssociatedUser.email == f'{project_data["user_email"]}').first()
    assert user_1.associated_user.user_id == project_data["user_id"]
    assert user_1.active == True
    assert user_1.role.code == "METADATA_ACCESS"

    #test new filter-set was created with same data except for name and added to project with no user id
    project = session.query(Project).filter(Project.id == project_id).first()
    assert project.searches[0].id != project_data["filter_set_id"]
    assert not project.searches[0].user_id
    assert not project.searches[0].user_source
    assert project.searches[0].filter_source == "manual"
    users_filter_set = session.query(Search).filter(Search.id == project_data["filter_set_id"]).first()
    assert project.searches[0].name == project.name + "_" + users_filter_set.name
    assert project.searches[0].description == users_filter_set.description
    assert project.searches[0].filter_object == users_filter_set.filter_object
    assert project.searches[0].graphql_object == users_filter_set.graphql_object



    INRG_request = session.query(Request).filter(Request.project_id == project_id).filter(Request.consortium_data_contributor.has(code="INRG")).first()
    assert INRG_request

    INSTRUCT_request = session.query(Request).filter(Request.project_id == project_id).filter(Request.consortium_data_contributor.has(code="INSTRUCT")).first()
    assert INSTRUCT_request
    
    #block project creation if request to pcdcanalysistools fails
    mock_requests_post(consortiums=["INSTRUCT", "INRG"], urls={config["GET_CONSORTIUMS_URL"]: 400})
    create_project_json = {
            "user_id": project_data["user_id"],
            "name": f"{__name__}_bad_project",
            "description": "This is an endpoint test project",
            "institution": "test university",
            "filter_set_ids": [project_data["filter_set_id"]],
            "associated_users_emails": []
    }
    create_project_response = client.post('/admin/projects', json=create_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert create_project_response.status_code == 500
    assert session.query(ConsortiumDataContributor).count() == 3
    assert session.query(Project).filter(Project.name == f"{__name__}_bad_project").count() == 0


@pytest.mark.order(3)
def test_admin_edit_project_users(session, client, login, project_data, mock_requests_post):
    
    mock_requests_post()

    roles_response = client.get("/admin/all_associated_user_roles", headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert roles_response.status_code == 200
    print(roles_response.json)
    for role in roles_response.json:
        if role["code"] == "DATA_ACCESS":
            data_access = role["code"]
        if role["code"] == "METADATA_ACCESS":
            metadata_access = role["code"]

    

    project_data["user_3_email"] = f"user_3@{__name__}.com"
    project_data["user_4_email"] = f"user_4@{__name__}.com"

    session.add(AssociatedUser(email=project_data["user_2_email"]))
    session.add(AssociatedUser(email=project_data["user_4_email"]))
    session.commit()

    #USER_1
    #not in table but in fence was added with user_id

    #USER_2
    #test add user with email in db and in fence and with data access
    add_user_2_response = client.post(
        "/admin/associated_user", 
        json={"users": [{"project_id": project_data["project_id"], "email": project_data["user_2_email"]}], 
              "role": data_access}, 
        headers={"Authorization": f'bearer {project_data["admin_id"]}'}
    )
    add_user_2_response.status_code == 200
    user_2 = session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_data["project_id"])\
                                                 .join(AssociatedUser, ProjectAssociatedUser.associated_user)\
                                                 .filter(AssociatedUser.email == project_data["user_2_email"]).first()
    assert user_2.associated_user.user_id == project_data["user_2_id"]
    assert user_2.active == True
    assert user_2.role.code == "DATA_ACCESS"

    #USER_3
    #test add user not in table and not in fence
    add_user_3_response = client.post(
        "/admin/associated_user", 
        json={"users": [{"project_id": project_data["project_id"], "email": project_data["user_3_email"]}], 
              "role": metadata_access}, 
        headers={"Authorization": f'bearer {project_data["admin_id"]}'}
    )
    add_user_3_response.status_code == 200
    user_3 = session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_data["project_id"])\
                                                 .join(AssociatedUser, ProjectAssociatedUser.associated_user)\
                                                 .filter(AssociatedUser.email == project_data["user_3_email"]).first() 
    assert user_3.associated_user.user_id == None
    assert user_3.active == True
    assert user_3.role.code == "METADATA_ACCESS"


    #ADMIN
    #add user with id and email in db and in fence
    add_admin_response = client.post(
        "/admin/associated_user", 
        json={"users": [{"project_id": project_data["project_id"], "email": project_data["admin_email"]}],}, 
        headers={"Authorization": f'bearer {project_data["admin_id"]}'}
    )
    add_admin_response.status_code == 200
    admin = session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_data["project_id"])\
                                                .join(AssociatedUser, ProjectAssociatedUser.associated_user)\
                                                .filter(AssociatedUser.email == project_data["admin_email"]).first()
    assert admin.associated_user.user_id == project_data["admin_id"]
    assert admin.active == True
    assert admin.role.code == "METADATA_ACCESS"

    #USER_4
    #email in DB not in fence
    add_user_4_response = client.post(
        "/admin/associated_user", 
        json={"users": [{"project_id": project_data["project_id"], "email": project_data["user_4_email"]}]}, 
        headers={"Authorization": f'bearer {project_data["admin_id"]}'}
    )
    add_user_4_response.status_code == 200
    user_4 = session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_data["project_id"])\
                                                 .join(AssociatedUser, ProjectAssociatedUser.associated_user)\
                                                 .filter(AssociatedUser.email == project_data["user_4_email"]).first()
    assert user_4.associated_user.user_id == None
    assert user_4.active == True
    assert user_4.role.code == "METADATA_ACCESS"


    #block adding duplicate user
    block_add_user_1_response = client.post(
        "/admin/associated_user", 
        json={"users": [{"project_id": project_data["project_id"], "email": project_data["user_email"]}],}, 
        headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    block_add_user_1_response.status_code == 200
    user_1 = session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_data["project_id"])\
                                                 .join(AssociatedUser, ProjectAssociatedUser.associated_user)\
                                                 .filter(AssociatedUser.email == project_data["user_email"]).all()
    user_1_data = session.query(AssociatedUser).filter(AssociatedUser.email == project_data["user_email"]).all()
    assert len(user_1) == 1
    user_1 = user_1[0]
    assert len(user_1_data) == 1

    #change user access
    user_1_data_acess_json = {
            "user_id": project_data["user_id"],
            "email": project_data["user_email"],
            "project_id": project_data["project_id"],
            "role": data_access
        }
    user_1_data_acess_response = client.put("/admin/associated_user_role", json=user_1_data_acess_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert user_1_data_acess_response.status_code == 200
    session.refresh(user_1)
    assert user_1.role.code == "DATA_ACCESS"


    #block removing project owner
    user_1_delete_json = {
            "user_id": project_data["user_id"],
            "email": project_data["user_email"],
            "project_id": project_data["project_id"],
        }
    user_1_delete_response = client.delete("/admin/remove_associated_user_from_project", json=user_1_delete_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert user_1_delete_response.status_code == 400
    session.refresh(user_1) 
    assert user_1.active == True
    assert user_1.role.code == "DATA_ACCESS"


    #remove user
    user_2_delete_json = {
        "user_id": project_data["user_2_id"],
        "email": project_data["user_2_email"],
        "project_id": project_data["project_id"],
    }
    user_2_delete_response = client.delete("/admin/remove_associated_user_from_project", json=user_2_delete_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert user_2_delete_response.status_code == 200
    session.refresh(user_2) 
    assert user_2.active == False
    assert user_2.role.code == "DATA_ACCESS"

    #TEST get all project_users and their roles by project_id
    project_users_response = client.get(f"/admin/project_users/{project_data['project_id']}", headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert project_users_response.status_code == 200

    correct_users = [{"email": project_data["user_email"], "role": "DATA_ACCESS"},
                     {"email": project_data["admin_email"], "role": "METADATA_ACCESS"},
                     {"email": project_data["user_3_email"], "role": "METADATA_ACCESS"},
                     {"email": project_data["user_4_email"], "role": "METADATA_ACCESS"}] 
    
    sorted_list1 = sorted(correct_users, key=lambda x: json.dumps(x, sort_keys=True))
    sorted_list2 = sorted(project_users_response.json, key=lambda x: json.dumps(x, sort_keys=True))
    
    assert sorted_list1 == sorted_list2
        



    #readd user
    readd_user_2_response = client.post(
        "/admin/associated_user", 
        json={"users": [{"project_id": project_data["project_id"], "email": project_data["user_2_email"]}], 
              "role": data_access}, 
        headers={"Authorization": f'bearer {project_data["admin_id"]}'}
    )
    readd_user_2_response.status_code == 200
    session.refresh(user_2)
    assert user_2.associated_user.user_id == project_data["user_2_id"]
    assert user_2.active == True
    assert user_2.role.code == "DATA_ACCESS"
    

@pytest.mark.order(4)
def test_admin_edit_project_state(session, client, project_data, mock_requests_post):           
    #TEST Moving project state with /admin/states
    #test some of the consortiums
    #test all of the consoritums
    revision_state = None
    approved_state = None
    data_available = None
    published_state = None
    get_states_response = client.get("/admin/states", headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    for state in get_states_response.json:
        if state["code"] == "REVISION":
            revision_state = state
        elif state["code"] == "APPROVED":
            approved_state = state
            project_data["approved_state_id"] = approved_state["id"]
        elif state["code"] == "DATA_AVAILABLE":
            project_data["data_available_state_id"] = state["id"]
            data_available = state
        elif state["code"] == "PUBLISHED":
            published_state = state 
            project_data["published_state_id"] = published_state["id"]
        elif state["code"] == "DATA_DOWNLOADED":
            project_data["data_downloaded_state_id"] = state["id"]
        

    update_project_state_INRG_approved_json = {"project_id": project_data["project_id"], "state_id": approved_state["id"], "consortiums": "INRG"}
    update_project_state_INRG_approved_response = client.post("/admin/projects/state", json=update_project_state_INRG_approved_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    update_project_state_INRG_approved_response.status_code == 200



    update_project_state_revison_json = {"project_id": project_data["project_id"], "state_id": revision_state["id"], "consortiums": "INSTRUCT"}
    update_project_state_revison_response = client.post("/admin/projects/state", json=update_project_state_revison_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    update_project_state_revison_response.status_code == 200

    """
    move project state to approved
    """
    #Test change all consortiums dont create duplicate state
    update_project_state_approved_json = {"project_id": project_data["project_id"], "state_id": approved_state["id"]}
    update_project_state_approved_response = client.post("/admin/projects/state", json=update_project_state_approved_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert update_project_state_approved_response.status_code == 200

    #Test change all consortiums
    update_project_state_data_available_json = {"project_id": project_data["project_id"], "state_id": data_available["id"]}
    update_project_state_data_available_response = client.post("/admin/projects/state", json=update_project_state_data_available_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert update_project_state_data_available_response.status_code == 200

    #Test all consoritums mov to final state
    update_project_state_published_json = {"project_id": project_data["project_id"], "state_id": published_state["id"]}
    update_project_state_published_response = client.post("/admin/projects/state", json=update_project_state_published_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert update_project_state_published_response.status_code == 200

    #test block all consoritums in final state
    update_project_state_data_available_json = {"project_id": project_data["project_id"], "state_id": data_available["id"]}
    update_project_state_data_available_response = client.post("/admin/projects/state", json=update_project_state_data_available_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert update_project_state_data_available_response.status_code == 400


    #test force endpoint to move all consotiums out of final state
    update_project_state_data_available_json = {"project_id": project_data["project_id"], "state_id": data_available["id"]}
    update_project_state_data_available_response = client.post("/admin/project/force-state-change", json=update_project_state_data_available_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert update_project_state_data_available_response.status_code == 200

    INRG = session.query(RequestState).filter(RequestState.request.has(Request.project_id == project_data["project_id"])).filter(RequestState.request.has(Request.consortium_data_contributor.has(ConsortiumDataContributor.code == "INRG"))).order_by(RequestState.create_date.asc()).all()
    INSTRUCT = session.query(RequestState).filter(RequestState.request.has(Request.project_id == project_data["project_id"])).filter(RequestState.request.has(Request.consortium_data_contributor.has(ConsortiumDataContributor.code == "INSTRUCT"))).order_by(RequestState.create_date.asc()).all()
    
    assert len(INSTRUCT) == 6
    assert len(INRG) == 5
    INRG_state = ["IN_REVIEW", "APPROVED", "DATA_AVAILABLE", "PUBLISHED", "DATA_AVAILABLE"]
    INSTRUCT_state = ["IN_REVIEW", "REVISION", "APPROVED", "DATA_AVAILABLE", "PUBLISHED", "DATA_AVAILABLE"]

    for i in range(len(INSTRUCT)):
        assert INSTRUCT[i].state.code == INSTRUCT_state[i]
    
    for i in range(len(INRG)):
        assert INRG[i].state.code == INRG_state[i]


@pytest.mark.order(5)
def test_admin_edit_filter_sets(session, client, project_data, mock_requests_post, login):
    """
    admin creates a filter_set with the corrections
    """
    from amanuensis.resources.userdatamodel.request_has_state import get_request_states
    
    session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "MAGIC").delete()
    session.commit()
    assert session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "MAGIC").count() == 0
    mock_requests_post(consortiums=["INSTRUCT", "INRG", "MAGIC"])

    """
    admin copies new search to the project
    """

    admin_copy_search_to_project_json = {
        "filtersetId": project_data["admin_filterset_id"],
        "projectId": project_data["project_id"]
    }
    admin_copy_search_to_project_response = client.post("admin/copy-search-to-project", json=admin_copy_search_to_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_copy_search_to_project_response.status_code == 200

    assert session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "MAGIC").count() == 1


    requests = session.query(Request).filter(Request.project_id == project_data["project_id"]).all()
    assert len(requests) == 3

    INRG = (
            session
            .query(Request)
            .filter(Request.project_id == project_data["project_id"])
            .join(ConsortiumDataContributor, Request.consortium_data_contributor)
            .filter(ConsortiumDataContributor.code == "INRG").first()
    )
    INSTRUCT = (
            session
            .query(Request)
            .filter(Request.project_id == project_data["project_id"])
            .join(ConsortiumDataContributor, Request.consortium_data_contributor)
            .filter(ConsortiumDataContributor.code == "INSTRUCT").first()
    )

    MAGIC = (
            session
            .query(Request)
            .filter(Request.project_id == project_data["project_id"])
            .join(ConsortiumDataContributor, Request.consortium_data_contributor)
            .filter(ConsortiumDataContributor.code == "MAGIC").first()
    )


    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "IN_REVIEW"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "IN_REVIEW"
    assert  get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "IN_REVIEW"

    login(project_data["admin_id"], project_data["admin_email"])
    update_project_state_approved_state_json = {"project_id": project_data["project_id"], "state_id": project_data["approved_state_id"]}
    update_project_state_approved_state_response = client.post("/admin/projects/state", json=update_project_state_approved_state_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    update_project_state_approved_state_response.status_code == 200

    filter_set_create_json = {
                "name":f"{__name__}_1_requests",
                "description":"",
                "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INSTRuCT"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
                "gqlFilter":{"AND":[{"IN":{"consortium":["INSTRuCT"]}},{"IN":{"sex":["Male"]}}]}
    }
    
    filter_set_create_response = client.post(f'/filter-sets?explorerId=1', json=filter_set_create_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert filter_set_create_response.status_code == 200

    id_1_requests = filter_set_create_response.json["id"]

    mock_requests_post(consortiums=["INSTRUCT"])

    admin_copy_search_to_project_json = {
                "filtersetId": id_1_requests,
                "projectId": project_data["project_id"]
    }
    admin_copy_search_to_project_response = client.post("admin/copy-search-to-project", json=admin_copy_search_to_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_copy_search_to_project_response.status_code == 200

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "IN_REVIEW"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "DEPRECATED"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"

    update_project_state_approved_state_json = {"project_id": project_data["project_id"], "state_id": project_data["approved_state_id"]}
    update_project_state_approved_state_response = client.post("/admin/projects/state", json=update_project_state_approved_state_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert update_project_state_approved_state_response.status_code == 200

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "APPROVED"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "DEPRECATED"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"

    filter_set_create_json = {
        "name":f"{__name__}_2_requests",
        "description":"",
        "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INSTRuCT", "INRG", "MAGIC"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
        "gqlFilter":{"AND":[{"IN":{"consortium":["INSTRuCT", "INRG"]}},{"IN":{"sex":["Male"]}}]}
    }
    filter_set_create_response = client.post(f'/filter-sets?explorerId=1', json=filter_set_create_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert filter_set_create_response.status_code == 200

    id_3_requests = filter_set_create_response.json["id"]

    mock_requests_post(consortiums=["INSTRUCT", "INRG"])

    admin_copy_search_to_project_json = {
                "filtersetId": id_3_requests,
                "projectId": project_data["project_id"]
    }
    admin_copy_search_to_project_response = client.post("admin/copy-search-to-project", json=admin_copy_search_to_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_copy_search_to_project_response.status_code == 200

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "IN_REVIEW"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "IN_REVIEW"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"

    #TEST if project is in data_available then if the filter-set is changed then state should go back to approved

    update_project_state_data_available_state_json = {"project_id": project_data["project_id"], "state_id": project_data["data_available_state_id"]}
    update_project_state_approved_state_response = client.post("/admin/projects/state", json=update_project_state_data_available_state_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "DATA_AVAILABLE"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "DATA_AVAILABLE"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"



    admin_copy_search_to_project_json = {
                "filtersetId": id_3_requests,
                "projectId": project_data["project_id"]
    }

    admin_copy_search_to_project_response = client.post("admin/copy-search-to-project", json=admin_copy_search_to_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_copy_search_to_project_response.status_code == 200

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "APPROVED"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "APPROVED"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"

    #TEST if project is in data_downloaded then if the filter-set is changed then state should go back to approved 
    #TEST if state is in deprecated then if the filter-set is changed then state should go back to approved

    mock_requests_post(consortiums=["INSTRUCT"])

    update_project_state_data_downloaded_state_json = {"project_id": project_data["project_id"], "state_id": project_data["data_downloaded_state_id"]}
    update_project_state_approved_state_response = client.post("/admin/projects/state", json=update_project_state_data_downloaded_state_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "DATA_DOWNLOADED"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "DATA_DOWNLOADED"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"

    admin_copy_search_to_project_json = {
                "filtersetId": id_1_requests,
                "projectId": project_data["project_id"]
    }

    admin_copy_search_to_project_response = client.post("admin/copy-search-to-project", json=admin_copy_search_to_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_copy_search_to_project_response.status_code == 200

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "IN_REVIEW"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "DEPRECATED"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"


    mock_requests_post(consortiums=["INSTRUCT", "INRG"])

    update_project_state_data_downloaded_state_json = {"project_id": project_data["project_id"], "state_id": project_data["data_available_state_id"]}
    update_project_state_approved_state_response = client.post("/admin/projects/state", json=update_project_state_data_downloaded_state_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "DATA_AVAILABLE"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "DEPRECATED"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"


    admin_copy_search_to_project_json = {
                "filtersetId": id_3_requests,
                "projectId": project_data["project_id"]
    }

    admin_copy_search_to_project_response = client.post("admin/copy-search-to-project", json=admin_copy_search_to_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_copy_search_to_project_response.status_code == 200

    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "IN_REVIEW"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "IN_REVIEW"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "DEPRECATED"




    #block filter-set change when project is in final state

    mock_requests_post(consortiums=["INSTRUCT", "INRG"])

    update_project_state_final_state_json = {"project_id": project_data["project_id"], "state_id": project_data["published_state_id"]}
    update_project_state_approved_state_response = client.post("/admin/projects/state", json=update_project_state_final_state_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    admin_copy_search_to_project_json = {
                "filtersetId": id_1_requests,
                "projectId": project_data["project_id"]
    }

    admin_copy_search_to_project_response = client.post("admin/copy-search-to-project", json=admin_copy_search_to_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_copy_search_to_project_response.status_code == 400

    
    #move project back to approved

    update_project_state_approved_state_json = {"project_id": project_data["project_id"], "state_id": project_data["approved_state_id"]}
    update_project_state_approved_state_response = client.post("/admin/project/force-state-change", json=update_project_state_approved_state_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert update_project_state_approved_state_response.status_code == 200
    assert get_request_states(session, request_id=INSTRUCT.id, latest=True, many=False).state.code == "APPROVED"
    assert get_request_states(session, request_id=INRG.id, latest=True, many=False).state.code == "APPROVED"
    assert get_request_states(session, request_id=MAGIC.id, latest=True, many=False).state.code == "APPROVED"




@pytest.mark.order(6)
def test_admin_upload_and_download_data(session, s3, client, login, project_data, mock_requests_post): 
    #admins can add add approved_url through put admin/projects (DEPRECATE) or admin/upload-data (REPLACE)
    #when a url is added and project is in data_available state users with DATA_ACCESS can download the data
    #user must be active on project

    data_available = session.query(State).filter(State.code == "DATA_AVAILABLE").first()

    """
    add approved_url to project
    """
    update_project_json = {
        "project_id": project_data["project_id"],
        "approved_url": "https://amanuensis-test-bucket.s3.amazonaws.com/test_key.txt"
    }
    update_project_response = client.put("/admin/projects", json=update_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'} )
    assert update_project_response.status_code == 200

    


    update_project_state_data_available_json = {"project_id": project_data["project_id"], "state_id": data_available.id}
    update_project_state_data_available_response = client.post("/admin/projects/state", json=update_project_state_data_available_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    update_project_state_data_available_response.status_code == 200

    


    if not s3:
        logger.error("aws creds not set up will not run presigned url test")
        assert False


    get_presigned_url_response = client.post("/admin/upload-file", json={"key": "data_1", "project_id": f"{project_data['project_id']}"}, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    
    assert get_presigned_url_response.status_code == 200

    url = get_presigned_url_response.json

    with open("tests/data/file.txt", "rb") as f:
        # Perform the PUT request to upload the file
        upload_file_response = requests.put(url, data=f)
    
    uploaded_file_response = s3.get_object(Bucket="amanuensis-upload-file-test-bucket", Key="data_1")

    assert upload_file_response.status_code == 200
    assert uploaded_file_response['ResponseMetadata']['HTTPStatusCode'] == 200


    """
    get download url
    """
    login(project_data["user_2_id"], project_data["user_2_email"])
    get_download_url_response = client.get(f"/download-urls/{project_data['project_id']}", headers={"Authorization": f'bearer {project_data["user_2_id"]}'})
    assert get_download_url_response.status_code == 200

    """
    check not active user 403's
    """
    user_2_delete_json = {
        "user_id": project_data["user_2_id"],
        "email": project_data["user_2_email"],
        "project_id": project_data["project_id"],
    }
    user_2_delete_response = client.delete("/admin/remove_associated_user_from_project", json=user_2_delete_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert user_2_delete_response.status_code == 200

    login(project_data["user_2_id"], project_data["user_2_email"])
    get_download_url_response = client.get(f"/download-urls/{project_data['project_id']}", headers={"Authorization": f'bearer {project_data["user_2_id"]}'})
    assert get_download_url_response.status_code == 404
    """
    get download url
    """
    login(project_data["admin_id"], project_data["admin_email"])
    get_download_url_response = client.get(f"/download-urls/{project_data['project_id']}", headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert get_download_url_response.status_code == 403


@pytest.mark.order(7)
def test_get_projects(session, client, login, project_data, mock_requests_post):
    #Test users can only see projects they are apart of
    #Test admin can see all projects
    #Test consortiums that are deprecated do not appear
    #Test delete project and that it doenst appear in search
    #Test when a user signs up and accesses get projects for first time their user_id is added to the DB



    login(project_data["admin_id"], project_data["admin_email"])
    admin_get_filter_sets_json = {"user_id": project_data["user_id"]}
    admin_get_filter_sets = client.get("/admin/filter-sets/user", json=admin_get_filter_sets_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_get_filter_sets.status_code == 200
    assert project_data["filter_set_id"] == admin_get_filter_sets.json["filter_sets"][0]["id"]

    mock_requests_post(consortiums=["INSTRUCT", "INRG"])

    create_project_json = {
            "user_id": project_data["user_2_id"],
            "name": f"{__name__}_2",
            "description": "This is an endpoint test project",
            "institution": "test university",
            "filter_set_ids": [project_data["filter_set_id"]],
            "associated_users_emails": [project_data["user_email"]]

    }
    create_project_response = client.post('/admin/projects', json=create_project_json, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert create_project_response.status_code == 200
    project_id = create_project_response.json['id']
    project_data["project_2_id"] = project_id

    #admin can see all projects
    login(project_data["admin_id"], project_data["admin_email"])
    admin_get_pojects_response = client.get("/projects?special_user=admin", headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert len(admin_get_pojects_response.json) >= 2


    login(project_data["user_2_id"], project_data["user_2_email"])
    user_2_get_projects_response = client.get("/projects", headers={"Authorization": f'bearer {project_data["user_2_id"]}'})
    print(user_2_get_projects_response.json)
    assert len(user_2_get_projects_response.json) == 1


    login(project_data["user_id"], project_data["user_email"])
    user_1_get_projects_response = client.get("/projects", headers={"Authorization": f'bearer {project_data["user_id"]}'})
    assert len(user_1_get_projects_response.json) == 2

    login(project_data["admin_id"], project_data["admin_email"])
    user_1_get_projects_response = client.get(f"/admin/projects_by_users/{project_data['user_id']}/{project_data['user_email']}", headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert user_1_get_projects_response.status_code == 200
    assert len(user_1_get_projects_response.json) == 2
    #Test deleting project
    login(project_data["admin_id"], project_data["admin_email"])
    delete_project_response = client.delete(f"/admin/delete-project/", json={"project_id": create_project_response.json['id']}, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert delete_project_response.status_code == 200

    
    admin_get_pojects_response = client.get("/projects?special_user=admin", headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    for project in admin_get_pojects_response.json:
        if create_project_response.json['id'] == project['id']:
            assert False
    
    login(project_data["user_id"], project_data["user_email"])
    user_1_get_projects_response = client.get("/projects", headers={"Authorization": f'bearer {project_data["user_id"]}'})
    assert len(user_1_get_projects_response.json) == 1


    
@pytest.mark.order(8)
def test_delete_filter_set(session, client, login, project_data):
    login(project_data['user_id'], project_data['user_email'])

    filter_set_update_json = {
        "name": "new_name",
        "description": "new_description",
        "filters": "new_filter_object",
        "graphql_object": "new_graphql_object"
    }
    filter_set_put_response = client.put(f'/filter-sets/{project_data["filter_set_id"]}', json=filter_set_update_json, headers={"Authorization": f'bearer {project_data["user_id"]}'})
    assert filter_set_put_response.status_code == 200

    filter_set_get_response = client.get(f'/filter-sets/{project_data["filter_set_id"]}?explorerId=1', headers={"Authorization": f'bearer {project_data["user_id"]}'})
    assert filter_set_get_response.status_code == 200
    assert len(filter_set_get_response.json["filter_sets"]) == 1
    assert filter_set_get_response.json["filter_sets"][0]["id"] == project_data["filter_set_id"]
    assert filter_set_get_response.json["filter_sets"][0]["name"] == filter_set_update_json["name"]
    assert filter_set_get_response.json["filter_sets"][0]["description"] == filter_set_update_json["description"]
    assert filter_set_get_response.json["filter_sets"][0]["filters"] == filter_set_update_json["filters"]
    #assert filter_set_get_response.json["filter_sets"][0]["graphql_object"] == filter_set_update_json["graphql_object"]


    filter_set_delete_response = client.delete(f'/filter-sets/{project_data["filter_set_id"]}', headers={"Authorization": f'bearer {project_data["user_id"]}'})
    assert filter_set_delete_response.status_code == 200

    filter_set_get_delete_search_response = client.get(f'/filter-sets/{project_data["filter_set_id"]}?explorerId=1', headers={"Authorization": f'bearer {project_data["user_id"]}'})
    assert filter_set_get_delete_search_response.status_code == 200
    assert len(filter_set_get_delete_search_response.json["filter_sets"]) == 0

    #add a new filter set for user 1 thats active
    login(project_data["user_id"], project_data["user_email"])

    create_filter_set_json = {
        "name": "new_name_2",
        "description": "new_description_2",
        "filters": "new_filter_object_2",
    }
    create_filter_set_response = client.post('/filter-sets', json=create_filter_set_json, headers={"Authorization": f'bearer {project_data["user_id"]}'})
    assert create_filter_set_response.status_code == 200

    #use admin endpoint to get deleted filter set
    login(project_data["admin_id"], project_data["admin_email"])
    admin_get_filter_set_response = client.get(f'/admin/filter-sets/user', json={"user_id": project_data["user_id"]}, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_get_filter_set_response.status_code == 200
    assert len(admin_get_filter_set_response.json["filter_sets"]) == 1

    admin_get_filter_set_response = client.get(f'/admin/filter-sets/user', json={"user_id": project_data["user_id"], "include_deleted": False}, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_get_filter_set_response.status_code == 200
    assert len(admin_get_filter_set_response.json["filter_sets"]) == 1

    admin_get_filter_set_response = client.get(f'/admin/filter-sets/user', json={"user_id": project_data["user_id"], "include_deleted": True}, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert admin_get_filter_set_response.status_code == 200
    assert len(admin_get_filter_set_response.json["filter_sets"]) == 2



@pytest.mark.order(9)
def test_notification_system(session, client, login, project_data):
    session.query(Notification).delete()
    session.query(NotificationLog).delete()
    
    session.commit() 

    # Original date
    expire_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    dont_expire_date = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S.%f")

    #TEST BAD datetime format
    bad_notification = client.post('/admin/create-notification', json={
        "message": "test notification 1",
        "expire_date": "2024-11-12 177:5:31.06723"
    }, headers={"Authorization": f'bearer {project_data["admin_id"]}'})
    assert bad_notification.status_code == 400


    notification_1 = client.post('/admin/create-notification', json={
        "message": "test notification 1",
        "expire_date": dont_expire_date
    }, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert notification_1.status_code == 200

    notification_1_query = session.query(NotificationLog).filter(NotificationLog.message == "test notification 1").all()
    assert len(notification_1_query) == 1

    login(project_data['user_id'], project_data['user_email'])

    user_1_sees_notification = client.get('/notifications', headers={"Authorization": f'bearer {project_data["user_id"]}'})

    assert user_1_sees_notification.status_code == 200

    user_1_sees_notification_query = session.query(Notification).filter(Notification.user_id == project_data['user_id']).all()

    assert len(user_1_sees_notification_query) == 1


    notification_2 = client.post('/admin/create-notification', json={
        "message": "test notification 2",
        "expire_date": dont_expire_date
    }, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert notification_2.status_code == 200

    user_1_sees_notification_2 = client.get('/notifications', headers={"Authorization": f'bearer {project_data["user_id"]}'})

    assert user_1_sees_notification_2.status_code == 200
    assert len(user_1_sees_notification_2.json) == 1

    user_1_sees_notification_2_query = session.query(Notification).filter(Notification.user_id == project_data['user_id']).all()
    assert len(user_1_sees_notification_2_query) == 2

    login(project_data['user_2_id'], project_data['user_2_email'])
    user_2_sees_notification = client.get('/notifications', headers={"Authorization": f'bearer {project_data["user_2_id"]}'})

    assert user_2_sees_notification.status_code == 200
    assert len(user_2_sees_notification.json) == 2

    notification_3 = client.post('/admin/create-notification', json={
        "message": "test notification 3",
        "expire_date": dont_expire_date
    }, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert notification_3.status_code == 200

    delete_notification_1 = client.delete(f'/admin/update-notification', json={"notification_log_id": [notification_3.json["id"]]}, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert delete_notification_1.status_code == 200

    login(project_data['user_id'], project_data['user_email'])
    user_1_doesnt_see_notification_3 = client.get('/notifications', headers={"Authorization": f'bearer {project_data["user_id"]}'})

    assert user_1_doesnt_see_notification_3.status_code == 200
    assert len(user_1_doesnt_see_notification_3.json) == 0

    #Test users dont see expired notifications
    notification_4 = client.post('/admin/create-notification', json={
        "message": "test notification 4",
        "expire_date": expire_date
    }, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert notification_4.status_code == 200

    login(project_data['user_id'], project_data['user_email'])
    user_1_doesnt_see_notification_4 = client.get('/notifications', headers={"Authorization": f'bearer {project_data["user_id"]}'})

    assert user_1_doesnt_see_notification_4.status_code == 200
    assert len(user_1_doesnt_see_notification_4.json) == 0
    

    update_user_1_notifcation_1_to_seen = client.put(f'/admin/update-notification', json={"notification_log_id": notification_1.json["id"], "user_id": project_data['user_id'], "seen": True}, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert update_user_1_notifcation_1_to_seen.status_code == 200

    #get notifications for user_1 where seen is true

    admin_get_route_filter_by_seen = client.get(f'/admin/notifications?user_id={project_data["user_id"]}&seen=True', headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert admin_get_route_filter_by_seen.status_code == 200
    assert len(admin_get_route_filter_by_seen.json) == 1

    get_all_notifications = client.get('/admin/notifications', headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert get_all_notifications.status_code == 200
    assert len(get_all_notifications.json) == 3


    #update expiration date on notification 4

    update_notification_4 = client.put(f'/admin/update-notification', json={"notification_log_id": notification_4.json["id"], "expire_date": dont_expire_date}, headers={"Authorization": f'bearer {project_data["admin_id"]}'})

    assert update_notification_4.status_code == 200

    login(project_data['user_id'], project_data['user_email'])
    user_1_sees_notification_4 = client.get('/notifications', headers={"Authorization": f'bearer {project_data["user_id"]}'})

    assert user_1_sees_notification_4.status_code == 200
    assert len(user_1_sees_notification_4.json) == 1

