from collections import OrderedDict
import os
import flask
from flask_cors import CORS
from sqlalchemy.orm import scoped_session

from userportaldatamodel.driver import SQLAlchemyDriver
from pcdcutils.signature import SignatureManager
from pcdcutils.errors import KeyPathInvalidError, NoKeyError
from pcdc_aws_client.boto import BotoManager
from cdislogging import get_logger
from cdispyutils.config import get_value
from gen3authz.client.arborist.client import ArboristClient
from amanuensis.errors import UserError
from amanuensis.models import migrate
from amanuensis.error_handler import get_error_response
from amanuensis.config import config
from amanuensis.settings import CONFIG_SEARCH_FOLDERS
import amanuensis.blueprints.misc
import amanuensis.blueprints.filterset
import amanuensis.blueprints.project
# import amanuensis.blueprints.message
import amanuensis.blueprints.admin
import amanuensis.blueprints.download_urls


# Can't read config yet. Just set to debug for now, else no handlers.
# Later, in app_config(), will actually set level based on config
logger = get_logger(__name__)

app = flask.Flask(__name__)
CORS(app=app, headers=["content-type", "accept"], expose_headers="*")


def warn_about_logger():
    raise Exception(
        "Flask 0.12 will remove and replace all of our log handlers if you call "
        "app.logger anywhere. Use get_logger from cdislogging instead."
    )


def app_init(
    app,
    settings="amanuensis.settings",
    root_dir=None,
    config_path=None,
    config_file_name=None,
):
    app.__dict__["logger"] = warn_about_logger

    app_config(
        app,
        settings=settings,
        root_dir=root_dir,
        config_path=config_path,
        file_name=config_file_name,
    )

    app_sessions(app)
    app_register_blueprints(app)


def app_sessions(app):
    ''' Override userdatamodel's `setup_db` since Alembic handles the migrations now. '''
    app.url_map.strict_slashes = False
    SQLAlchemyDriver.setup_db = lambda _: None
    app.db = SQLAlchemyDriver(config["DB"])
    app.scoped_session = scoped_session(app.db.Session)


def app_register_blueprints(app):
    app.register_blueprint(amanuensis.blueprints.admin.blueprint, url_prefix="/admin")
    app.register_blueprint(amanuensis.blueprints.download_urls.blueprint, url_prefix="/download-urls")
    app.register_blueprint(amanuensis.blueprints.filterset.blueprint, url_prefix="/filter-sets")
    app.register_blueprint(amanuensis.blueprints.project.blueprint, url_prefix="/projects")

    # Disable for now since they are not used yet
    # app.register_blueprint(amanuensis.blueprints.message.blueprint, url_prefix="/message")
    
    amanuensis.blueprints.misc.register_misc(app)


def app_config(
    app, settings="amanuensis.settings", root_dir=None, config_path=None, file_name=None
):
    """
    Set up the config for the Flask app.
    """
    if root_dir is None:
        root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    logger.info("Loading settings...")
    # not using app.config.from_object because we don't want all the extra flask cfg
    # vars inside our singleton when we pass these through in the next step
    settings_cfg = flask.Config(app.config.root_path)
    settings_cfg.from_object(settings)

    # dump the settings into the config singleton before loading a configuration file
    config.update(dict(settings_cfg))

    # load the configuration file, this overwrites anything from settings/local_settings
    config.load(
        config_path=config_path,
        search_folders=CONFIG_SEARCH_FOLDERS,
        file_name=file_name,
    )

    # load all config back into flask app config for now, we should PREFER getting config
    # directly from the amanuensis config singleton in the code though.
    app.config.update(**config._configs)

    _setup_hubspot_key(app)
    _setup_arborist_client(app)
    _setup_data_endpoint_and_boto(app)

    # app.storage_manager = StorageManager(config["STORAGE_CREDENTIALS"], logger=logger)

    app.debug = config["DEBUG"]
    # Following will update logger level, propagate, and handlers
    get_logger(__name__, log_level="debug" if config["DEBUG"] == True else "info")

    # load private key for cross-service access
    key_path = config.get("PRIVATE_KEY_PATH", None)

    try:
        config["RSA_PRIVATE_KEY"] = SignatureManager(key_path=key_path).get_key()
    except NoKeyError:
        logger.warn('AMANUENSIS_PUBLIC_KEY not found.')
        pass
    except KeyPathInvalidError:
        logger.warn('AMANUENSIS_PUBLIC_KEY_PATH invalid.')
        pass

    # _check_s3_buckets(app)


def _setup_data_endpoint_and_boto(app):
    if "AWS_CREDENTIALS" in config and len(config["AWS_CREDENTIALS"]) > 0:
        #TODO why does it need to be the first one? (use the key value in the object instead of making it a list)
        value = list(config["AWS_CREDENTIALS"].values())[0]
        app.boto = BotoManager(value, logger=logger)
        logger.info("BotoManager initialized")
    else:
        logger.warning("Missing credentials for BotoManager, delivery of data will fail.")

def _setup_arborist_client(app):
    if app.config.get("ARBORIST"):
        app.arborist = ArboristClient(arborist_base_url=config["ARBORIST"])

def _setup_hubspot_key(app):
    if app.config.get("HUBSPOT"):
        if "API_KEY" in config["HUBSPOT"]:
            app.hubspot_api_key = config["HUBSPOT"]["API_KEY"]
        # else:
            #TODO throw error

@app.errorhandler(Exception)
def handle_error(error):
    """
    Register an error handler for general exceptions.
    """
    return get_error_response(error)

@app.teardown_appcontext
def remove_scoped_session(*args, **kwargs):
    if hasattr(app, "scoped_session"):
        try:
            app.scoped_session.remove()
        except Exception as exc:
            logger.warning(f"could not remove app.scoped_session. Error: {exc}")



