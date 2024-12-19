
from cdislogging import get_logger
from userportaldatamodel.driver import SQLAlchemyDriver
from amanuensis.settings import CONFIG_SEARCH_FOLDERS
from amanuensis.config import config
from amanuensis.resources.filter_sets import check_filter_sets
logger = get_logger(__name__, log_level="info")



def main():
    config.load(
        search_folders=CONFIG_SEARCH_FOLDERS
    )
    SQLAlchemyDriver.setup_db = lambda _: None
    db = SQLAlchemyDriver(config["DB"])
    with db.session as session:
        check_filter_sets(session)
        session.commit()




if __name__ == "__main__":
    main()