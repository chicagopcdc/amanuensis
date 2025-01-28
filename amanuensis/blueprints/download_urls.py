import flask

from cdislogging import get_logger

from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError, UserError, NotFound, InternalError, Forbidden
from pcdc_aws_client.utils import get_s3_key_and_bucket

from amanuensis.resources.userdatamodel.project import get_projects
from amanuensis.resources.userdatamodel.project_has_associated_user import get_project_associated_users
from amanuensis.resources.request import change_request_state

from amanuensis.config import config


logger = get_logger(__name__)

blueprint = flask.Blueprint("download-urls", __name__)


@blueprint.route("/<project_id>", methods=["GET"])
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

    if not flask.current_app.s3_boto:
        raise InternalError("BotoManager not found. Check the AWS credentials are set in the config and have the correct permissions.")

    # Check param is present
    if not project_id:
        raise UserError("A project_id is needed to retrieve the correct URL")

    with flask.current_app.db.session as session:

        project = get_projects(session, id=project_id, many=False, throw_not_found=True)

        # Get download url from project table
        storage_url = project.approved_url
        if not storage_url:
            raise NotFound("The project with id {} doesn't seem to have a loaded file with approved data.".format(project_id)) 

        user = get_project_associated_users(session, project_id, associated_user_user_id=logged_user_id, associated_user_email=logged_user_email, many=False, throw_not_found=True)
        
        if user.role.code != "DATA_ACCESS":
            raise Forbidden("User {} is not allowed to download data from project {}".format(logged_user_email, project_id))
        
        # TODO - assign on file creation metadata to S3 file (play with indexd since it probably supports it). 
        # Check that user has access to that file before creating the presigned url. The responsibility is on the admin here and a wrong 
        # project_id in the API call could assign data download rights to the wrong user


        #check if project is in fianl state or in Data Download state before attempting to change state
        change_request_state(session, project_id, state_code="DATA_DOWNLOADED")
            
        session.commit()

        # Create pre-signed URL for downalod
        s3_info = get_s3_key_and_bucket(storage_url)
        if s3_info is None:
            raise NotFound("The S3 bucket and key information cannot be extracted from the URL {}".format(storage_url))

        result = flask.current_app.s3_boto.presigned_url(s3_info["bucket"], s3_info["key"], "1800", {}, "get_object")
        return flask.jsonify({"download_url": result})









