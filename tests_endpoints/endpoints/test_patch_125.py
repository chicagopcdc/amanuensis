import pytest
from mock import patch
from cdislogging import get_logger
from amanuensis.models import *
from amanuensis.schema import *
from datetime import datetime
import time
from amanuensis.blueprints.filterset import UserError


def test_admin_creates_project_with_filter_set_project_owner_dont_match(session, client, fence_get_users_mock, fence_users):
    with \
    patch("amanuensis.resources.admin.admin_associated_user.fence.fence_get_users", side_effect=fence_get_users_mock), \
    patch("amanuensis.blueprints.project.fence_get_users", side_effect=fence_get_users_mock), \
    patch('amanuensis.blueprints.filterset.current_user', id=200, username="admin@uchicago.edu"):
        filter_set_create_json = {
            "name":f"{__name__}",
            "description":"",
            "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INSTRuCT"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
            "gqlFilter":{"AND":[{"IN":{"consortium":["INSTRuCT"]}},{"IN":{"sex":["Male"]}}]}
        }
        filter_set_create_response = client.post(f'/filter-sets?explorerId=1', json=filter_set_create_json, headers={"Authorization": 'bearer 106'})
        assert filter_set_create_response.status_code == 200

        filter_set_id = filter_set_create_response.json["id"]

        with \
        patch('amanuensis.resources.consortium_data_contributor.get_consortium_list', return_value=["INSTRuCT"]):
            create_project_json = {
                "user_id": 106,
                "name": f"{__name__}",
                "description": f"this is the project for {__name__}",
                "institution": "test university",
                "filter_set_ids": [filter_set_id],
                "associated_users_emails": []

            }
            create_project_response = client.post('/admin/projects', json=create_project_json, headers={"Authorization": 'bearer 200'})
            assert create_project_response.status_code == 200
            project_id = create_project_response.json['id']
        
        requests = session.query(Request).filter(Request.project_id == project_id).all()

        assert len(requests) == 1