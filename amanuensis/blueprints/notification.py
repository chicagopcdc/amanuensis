import flask

from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import NotificationSchema
from amanuensis.resources import notification
from cdislogging import get_logger

logger = get_logger(__name__)

blueprint = flask.Blueprint("notification", __name__)



@blueprint.route("/new", methods=["GET"])
def retrieve_unseen():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )

    notification_schema = NotificationLogSchema(many=True)
    unseen = notification.get_unseen_notifications(logged_user_id)
    return flask.jsonify(notification_schema.dump(unseen))




