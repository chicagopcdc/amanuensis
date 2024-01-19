import flask

# from amanuensis.auth import login_required, current_token
# from amanuensis.errors import Unauthorized, UserError, NotFound
# from amanuensis.models import Application, Certificate
from amanuensis.resources.request import get
from amanuensis.config import config
from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import RequestSchema
from cdislogging import get_logger

blueprint = flask.Blueprint("requests", __name__)

logger = get_logger(__name__)


# DISABLE FOR NOW SINCE ONLY ADMIN CAN CREATE A PROJECT
# @blueprint.route("/", methods=["GET"])
# def get_request():
#     """

#     """
#     try:
#         logged_user_id = current_user.id
#     except AuthError:
#         logger.warning(
#             "Unable to load or find the user, check your token"
#         )

#     #TODO check if user is EC consortium member or not
#     consortium = flask.request.args.get('consortium', None)

#     request_schema = RequestSchema(many=True)
#     return flask.jsonify(request_schema.dump(get(logged_user_id, consortium)))


