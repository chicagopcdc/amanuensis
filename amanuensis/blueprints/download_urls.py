import flask

from cdislogging import get_logger

from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError, UserError, NotFound, InternalError, Forbidden
from amanuensis.resources.project import get_by_id
from amanuensis.resources.admin import update_project_state, get_by_code
from pcdc_aws_client.utils import get_s3_key_and_bucket


from amanuensis.config import config


logger = get_logger(__name__)

blueprint = flask.Blueprint("download-urls", __name__)


@blueprint.route("/<path:project_id>", methods=["GET"])
def download_data(project_id):
    """
    Get a presigned url to download a file given a project_id.
    """

    try:
        logged_user_id = current_user.id
        logged_user_email = current_user.username
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )

    if not flask.current_app.boto:
        raise InternalError("BotoManager not found. Check the AWS credentials are set in the config and have the correct permissions.")

    # Check param is present
    if not project_id:
        raise UserError("A project_id is needed to retrieve the correct URL")

    project = get_by_id(logged_user_id, project_id)
    if not project:
        raise NotFound("The project with id {} has not been found.".format(project_id))

    associated_users_ids = []
    associated_users_emails = []
    for associated_user_role in project.associated_users_roles:
        if associated_user_role.active and associated_user_role.associated_user.user_id and associated_user_role.role.code == "DATA_ACCESS":
            associated_users_ids.append(associated_user_role.associated_user.user_id)
        if associated_user_role.active and associated_user_role.associated_user.email and associated_user_role.role.code == "DATA_ACCESS":
            associated_users_emails.append(associated_user_role.associated_user.email)
    if logged_user_id not in associated_users_ids and logged_user_email not in associated_users_emails:
        raise Forbidden("The user is not in the list of associated_users that signed the DUA. Please reach out to pcdc_help@lists.uchicago.edu")

    # Get download url from project table
    storage_url = project.approved_url
    if not storage_url:
        raise NotFound("The project with id {} doesn't seem to have a loaded file with approved data.".format(project_id))


    # TODO - assign on file creation metadata to S3 file (play with indexd since it probably supports it). 
    # Check that user has access to that file before creating the presigned url. The responsibility is on the admin here and a wrong 
    # project_id in the API call could assign data download rights to the wrong user


    
    data_downloaded_state = get_by_code("DATA_DOWNLOADED")
    if not data_downloaded_state:
        raise NotFound("Data download state does not exist. Please reach out to pcdc_help@lists.uchicago.edu")
    else:
        update_project_state(project_id, data_downloaded_state.id)

    # Create pre-signed URL for downalod
    s3_info = get_s3_key_and_bucket(storage_url)
    if s3_info is None:
        raise NotFound("The S3 bucket and key information cannot be extracted from the URL {}".format(storage_url))

    result = flask.current_app.boto.presigned_url(s3_info["bucket"], s3_info["key"], "1800", {}, "get_object")
    return flask.jsonify({"download_url": result})









