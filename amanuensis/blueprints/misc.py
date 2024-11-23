from cdiserrors import UnhealthyCheck
import flask
from cdislogging import get_logger
from amanuensis.version_data import VERSION, COMMIT
from sqlalchemy import text

logger = get_logger(__name__)

def register_misc(app):
    @app.route("/_status", methods=["GET"])
    def health_check():
        """
        Health Check.
        """
        with flask.current_app.db.session as session:
            try:
                session.execute(text("SELECT 1"))
            except Exception as e:
                logger.error(f"Failed health check: {e}")
                raise UnhealthyCheck("Unhealthy")

        return "Healthy", 200

    @app.route("/_version", methods=["GET"])
    def version():
        """
        Return the version of this service.
        """

        base = {"version": VERSION, "commit": COMMIT}

        return flask.jsonify(base), 200
