import flask
from cdislogging import get_logger
from amanuensis.config import config
from amanuensis.resources.fence import fence_get_users
from amanuensis.resources.userdatamodel.project import update_project, create_project, get_projects
from amanuensis.resources.userdatamodel.search import get_filter_sets
from amanuensis.resources.request import project_requests_from_filter_sets
from amanuensis.resources.associated_user import add_associated_users
from amanuensis.resources.request import change_request_state
from amanuensis.resources.message import send_email
from amanuensis.resources.userdatamodel.project_has_associated_user import get_project_associated_users 
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

def send_project_email(session, project=None, project_id=None):
    #send email to all active project users with role DATA_ACCESS and have signed into portal before
    
    if not project:
        project = get_projects(session, id=project_id, many=False, throw_not_found=True)

    project_users_with_data_access = [project_user.associated_user.email for project_user in get_project_associated_users(session, project_id=(project_id if project_id else project.id), role_code="DATA_ACCESS", many=True)]
    
    try:
        project_users_logged_into_fence = fence_get_users(usernames=project_users_with_data_access)["users"]
        recipients = []
        first_names = ""
        
        for i in range(len(project_users_logged_into_fence)):
            
            if i == len(project_users_logged_into_fence) - 1 and len(project_users_logged_into_fence) > 1:
                #remove the last commma from first names before adding last name
                first_names = first_names[:-2]
                first_names += " and " + project_users_logged_into_fence[i]["first_name"] + ","
            
            else:
                
                first_names += project_users_logged_into_fence[i]["first_name"] + ", "
            
            recipients.append(project_users_logged_into_fence[i]["username"])
            
        email_body = config["DATA_AVAILABLE_NOTIFICATION"]["EMAIL_BODY"].format(users=first_names, project_name=project.name, project_id=project.description)
        send_email(config["DATA_AVAILABLE_NOTIFICATION"]["EMAIL_SUBJECT"], email_body, recipients=recipients)
    except Exception as e:
        logger.error(f"Failed to send email to {project_users_with_data_access}: {e}")
        raise UserError("Failed to send email notification to project users")

def upload_file(session, key, project_id, expires=None):

    try:
        presigned_url = flask.current_app.s3_boto.presigned_url(config["AWS_CREDENTIALS"]["DATA_DELIVERY_S3_BUCKET"]["bucket_name"], key, expires, {}, method="put_object")

    except Exception as e:
        logger.error(f"Failed to generate presigned url: {e}")
        raise InternalError("Failed to generate presigned url")
    
    update_project(session, project_id, approved_url=f'https://{config["AWS_CREDENTIALS"]["DATA_DELIVERY_S3_BUCKET"]["bucket_name"]}.s3.amazonaws.com/{key}')
    
    return presigned_url








