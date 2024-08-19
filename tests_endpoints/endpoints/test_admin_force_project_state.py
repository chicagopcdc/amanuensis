import pytest
from mock import patch
from amanuensis.models import *
from amanuensis.schema import *
from sqlalchemy import desc

@pytest.fixture(scope="module", autouse=True)
def set_up_filter_set(client):
    with \
    patch('amanuensis.blueprints.filterset.current_user', id=108, username="endpoint_user_8@test.com"):
        filter_set_create_1_json = {
            "name":f"{__name__}",
            "description":"",
            "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
            "gqlFilter":{"AND":[{"IN":{"consortium":["INRG"]}},{"IN":{"sex":["Male"]}}]}
        }
        filter_set_create_response = client.post(f'/filter-sets?explorerId=1', json=filter_set_create_1_json, headers={"Authorization": 'bearer 108'})
        assert filter_set_create_response.status_code == 200

        filter_set_id_1 = filter_set_create_response.json["id"]

        yield filter_set_id_1


@pytest.fixture(scope="module", autouse=True)
def set_up_project(set_up_filter_set, client, fence_get_users_mock, session):
    with \
    patch("amanuensis.resources.admin.admin_associated_user.fence.fence_get_users", side_effect=fence_get_users_mock), \
    patch('amanuensis.blueprints.admin.current_user', id=200, username="admin@uchicago.edu"), \
    patch('amanuensis.resources.consortium_data_contributor.get_consortium_list', return_value=["INRG"]):
        create_project_json = {
            "user_id": 108,
            "name": f"{__name__}",
            "description": f"this is the project for {__name__}",
            "institution": "test university",
            "filter_set_ids": [set_up_filter_set],
            "associated_users_emails": []
        }
        create_project_response = client.post('/admin/projects', json=create_project_json, headers={"Authorization": 'bearer 200'})
        
        assert create_project_response.status_code == 200

        rejected_state = session.query(State).filter(State.code == "REJECTED").first()
        
        update_project_state_json = {"project_id": create_project_response.json['id'], "state_id": rejected_state.id}
        
        update_project_state_response = client.post("/admin/projects/state", json=update_project_state_json, headers={"Authorization": 'bearer 200'})
        update_project_state_response.status_code == 200

    yield create_project_response.json['id'], update_project_state_response.json[0]['id']

def test_force_admin_project_state_change(client, session, set_up_project, fence_get_users_mock):
    with \
    patch('amanuensis.blueprints.admin.current_user', id=200, username="admin@uchicago.edu"):
        
        project_id = set_up_project[0]

        request_id = set_up_project[1]

        #test that state cant be changed

        approved_state = session.query(State).filter(State.code == "APPROVED").first()

        update_project_state_json = {"project_id": project_id, "state_id": approved_state.id}

        update_project_state_failed_response = client.post("/admin/projects/state", json=update_project_state_json, headers={"Authorization": 'bearer 200'})
        
        assert update_project_state_failed_response.status_code == 400


        #test that state can be changed with special route

        update_project_state_force_response = client.post("/admin/project/force-state-change", json=update_project_state_json, headers={"Authorization": 'bearer 200'})

        assert update_project_state_force_response.status_code == 200

        current_state = session.query(RequestState).filter(RequestState.request_id == request_id).order_by(desc(RequestState.create_date)).first().state.code


        assert current_state == "APPROVED"

    
