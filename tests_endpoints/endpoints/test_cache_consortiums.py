"""
This file tests adding consortiums to the amanuensis DB when creating a project request or changing filter-set 
when the consortiums returned from guppy are not in the amanuensis DB

test 1: add a consortium when creating a data request

test 2: add a consortium when changing a filter-set
"""

import pytest
import json
from mock import patch, Mock
from cdislogging import get_logger
from amanuensis.models import *
from amanuensis.schema import *

logger = get_logger(logger_name=__name__)





@pytest.fixture(scope="module", autouse=True)
def get_fake_consortium(session):
    def get_consortium(consortium):
         return session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == consortium).first()
    
    yield get_consortium

@pytest.fixture(scope="module", autouse=True)
def set_up_filter_set(client):
    with \
    patch('amanuensis.blueprints.filterset.current_user', id=108, username="endpoint_user_8@test.com"):
        filter_set_create_1_json = {
            "name":f"{__name__}",
            "description":"",
            "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["FAKE_CONSORTIUM_1"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
            "gqlFilter":{"AND":[{"IN":{"consortium":["FAKE_CONSORTIUM_1"]}},{"IN":{"sex":["Male"]}}]}
        }
        filter_set_create_response = client.post(f'/filter-sets?explorerId=1', json=filter_set_create_1_json, headers={"Authorization": 'bearer 108'})
        assert filter_set_create_response.status_code == 200

        filter_set_id_1 = filter_set_create_response.json["id"]

        filter_set_create_2_json = {
            "name":f"{__name__}",
            "description":"",
            "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["FAKE_CONSORTIUM_2"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
            "gqlFilter":{"AND":[{"IN":{"consortium":["FAKE_CONSORTIUM_2"]}},{"IN":{"sex":["Male"]}}]}
        }
        filter_set_create_response = client.post(f'/filter-sets?explorerId=1', json=filter_set_create_2_json, headers={"Authorization": 'bearer 108'})
        assert filter_set_create_response.status_code == 200

        filter_set_id_2 = filter_set_create_response.json["id"]

        yield [filter_set_id_1, filter_set_id_2]


def test_build_project_with_non_existent_consortium(set_up_filter_set, client, fence_get_users_mock, get_fake_consortium):
    with \
    patch("amanuensis.resources.admin.admin_associated_user.fence.fence_get_users", side_effect=fence_get_users_mock), \
    patch('amanuensis.blueprints.admin.current_user', id=200, username="admin@uchicago.edu"), \
    patch('amanuensis.resources.consortium_data_contributor.get_consortium_list', return_value=["FAKE_CONSORTIUM_1"]):
        from amanuensis import config
        create_project_json = {
            "user_id": 108,
            "name": f"{__name__}",
            "description": f"this is the project for {__name__}",
            "institution": "test university",
            "filter_set_ids": [set_up_filter_set[0]],
            "associated_users_emails": []

        }
        create_project_response = client.post('/admin/projects', json=create_project_json, headers={"Authorization": 'bearer 200'})
        
        assert create_project_response.status_code == 200
        
        assert get_fake_consortium("FAKE_CONSORTIUM_1")

def test_change_filter_set_with_non_existent_consortium(set_up_filter_set, client, get_fake_consortium, session):
     
    project_id = session.query(Project).filter(Project.name == f"{__name__}").first().id

    filter_set_id = set_up_filter_set[1]

    copy_search_to_project_json = {
        "filtersetId": filter_set_id,
        "projectId": project_id
    }
    with \
    patch('amanuensis.blueprints.admin.current_user', id=200, username="admin@uchicago.edu"), \
    patch('amanuensis.resources.consortium_data_contributor.get_consortium_list', return_value=["FAKE_CONSORTIUM_2"]):
        
        copy_search_to_project_response = client.post("admin/copy-search-to-project", json=copy_search_to_project_json, headers={"Authorization": 'bearer 200'})
        assert copy_search_to_project_response.status_code == 200

        assert get_fake_consortium("FAKE_CONSORTIUM_2")
