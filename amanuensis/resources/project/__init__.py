import flask
from cdislogging import get_logger
from amanuensis.config import config
from amanuensis.resources.fence import fence_get_users
from amanuensis.resources.userdatamodel.project import update_project, create_project
from amanuensis.resources.userdatamodel.search import get_filter_sets
from amanuensis.resources.request import project_requests_from_filter_sets
from amanuensis.resources.associated_user import add_associated_users
from amanuensis.errors import UserError, InternalError



logger = get_logger(__name__)



def create(current_session, logged_user_id, is_amanuensis_admin, name, description, filter_set_ids, explorer_id, institution, associated_users_emails):
    # retrieve all the filter_sets associated with this project
    if not fence_get_users(ids=[logged_user_id])["users"]:
        raise UserError(f"the user id {logged_user_id} does not exist in the commons")

    project = create_project(current_session, logged_user_id, description, name, institution)

    filter_sets = get_filter_sets(
        current_session=current_session, 
        filter_by_source_type=(not is_amanuensis_admin), 
        user_id=logged_user_id if not is_amanuensis_admin else None, 
        explorer_id=explorer_id if not is_amanuensis_admin else None,
        throw_not_equal=True,
        id=filter_set_ids
    )



    project_requests_from_filter_sets(session=current_session, filter_sets=filter_sets, project=project)
 
    associated_users = [{"project_id": project.id, "email": email } for email in associated_users_emails] + [{"project_id": project.id, "id": logged_user_id}]

    add_associated_users(session=current_session, users=associated_users)
    
    return project



def upload_file(session, key, project_id, expires=None):

    bucket = list(config['AWS_CREDENTIALS'].keys())[0]

    try:
        presigned_url = flask.current_app.boto.presigned_url(bucket, key, expires, bucket, method="put_object")

    except Exception as e:
        logger.error(f"Failed to generate presigned url: {e}")
        raise InternalError("Failed to generate presigned url")
    
    update_project(session, project_id, approved_url=f"https://{bucket}.s3.amazonaws.com/{key}")

    return presigned_url








