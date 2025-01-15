import argparse
from cdislogging import get_logger
from userportaldatamodel.driver import SQLAlchemyDriver
from amanuensis.settings import CONFIG_SEARCH_FOLDERS
from amanuensis.config import config
from amanuensis.resources.filter_sets import check_filter_sets

logger = get_logger(__name__, log_level="info")



def main(config_file_name=None):
    config.load(
        search_folders=CONFIG_SEARCH_FOLDERS,
        file_name=config_file_name
    )
    SQLAlchemyDriver.setup_db = lambda _: None
    db = SQLAlchemyDriver(config["DB"])
    with db.session as session:
        check_filter_sets(session)
        session.commit()




if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Run the filter sets checker.")
    parser.add_argument(
        "--file_name",
        help="Optional configuration file name to load.",
        default=None
    )
    args = parser.parse_args()
    main(config_file_name=args.file_name)