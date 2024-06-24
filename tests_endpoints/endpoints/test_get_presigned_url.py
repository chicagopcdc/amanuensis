import pytest
from mock import patch
from cdislogging import get_logger
from amanuensis.models import *
from amanuensis.schema import *
import requests

logger = get_logger(logger_name=__name__)

@pytest.fixture(scope="module", autouse=True)
def s3(app_instance):
    try: 

        s3 = app_instance.boto.s3_client
        bucket_name = 'amanuensis-upload-file-test-bucket'

        # Check if the bucket exists
        def bucket_exists(bucket_name):
            response = s3.list_buckets()
            for bucket in response['Buckets']:
                if bucket['Name'] == bucket_name:
                    return True
            return False

        # Create bucket if it doesn't exist
        if not bucket_exists(bucket_name):
            s3.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' created.")

        # Delete file if it exists
        try:
            s3.delete_object(Bucket=bucket_name, Key='data_1')
            logger.info("File 'data_1' deleted.")
        except s3.exceptions.NoSuchKey:
            logger.info("File 'data_1' does not exist.")

    
    except Exception as e:
        logger.error(f"Failed to set up s3 bucket, tests will fail {e}")
        yield None

    yield s3

    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
            logger.info(f"deleted {obj['Key']}")
    
    s3.delete_bucket(Bucket=bucket_name)
    logger.info(f"delete bucket {bucket_name}")



    



@pytest.fixture(scope="module", autouse=True)
def set_up_project(client, fence_get_users_mock):
    with \
    patch("amanuensis.resources.admin.admin_associated_user.fence.fence_get_users", side_effect=fence_get_users_mock), \
    patch("amanuensis.blueprints.project.fence_get_users", side_effect=fence_get_users_mock):
        #create a filter-set with 1 consortium
        with \
        patch('amanuensis.blueprints.filterset.current_user', id=107, username="endpoint_user_7@test.com"):
            filter_set_create_json = {
                "name":f"{__name__}",
                "description":"",
                "filters":{"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INSTRuCT"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
                "gqlFilter":{"AND":[{"IN":{"consortium":["INSTRuCT"]}},{"IN":{"sex":["Male"]}}]}
            }
            filter_set_create_response = client.post(f'/filter-sets?explorerId=1', json=filter_set_create_json, headers={"Authorization": 'bearer 107'})
            assert filter_set_create_response.status_code == 200

            filter_set_id = filter_set_create_response.json["id"]


        with \
        patch('amanuensis.blueprints.admin.current_user', id=200, username="admin@uchicago.edu"), \
        patch('amanuensis.resources.consortium_data_contributor.get_consortium_list', return_value=["INSTRuCT"]):
            create_project_json = {
                "user_id": 107,
                "name": f"{__name__}",
                "description": f"this is the project for {__name__}",
                "institution": "test university",
                "filter_set_ids": [filter_set_id],
                "associated_users_emails": []

            }
            create_project_response = client.post('/admin/projects', json=create_project_json, headers={"Authorization": 'bearer 200'})
            assert create_project_response.status_code == 200
            project_id = create_project_response.json['id']
    
    yield project_id


def test_get_presigned_url(s3, set_up_project, app_instance, client):
    if not s3:
        logger.error("aws creds not set up will not run presigned url test")
        assert False
    
    project_id = set_up_project

    get_presigned_url_response = client.post("/admin/upload-file", json={"bucket": "amanuensis-upload-file-test-bucket", "key": "data_1", "project_id": f"{project_id}"}, headers={"Authorization": 'bearer 200'})
    
    
    url = get_presigned_url_response.json

    with open("tests_endpoints/endpoints/data/file.txt", "rb") as f:
        # Perform the PUT request to upload the file
        upload_file_response = requests.put(url, data=f)
    
    uploaded_file_response = s3.get_object(Bucket="amanuensis-upload-file-test-bucket", Key="data_1")

    assert upload_file_response.status_code == 200