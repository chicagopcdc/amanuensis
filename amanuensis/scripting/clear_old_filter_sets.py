
from cdislogging import get_logger
from userportaldatamodel.driver import SQLAlchemyDriver
from amanuensis.settings import CONFIG_SEARCH_FOLDERS
from amanuensis.config import config
from amanuensis.resources.filter_sets import clear_out_unused_filter_sets
import argparse
logger = get_logger(__name__, log_level="info")


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Run the filter sets checker.")
    parser.add_argument(
        "--file_name",
        help="Optional configuration file name to load.",
        default=None
    )
    return parser.parse_args(args)



def main(args=None):
    try:
        config_file_name = parse_args(args).file_name

        config.load(
            search_folders=CONFIG_SEARCH_FOLDERS,
            file_name=config_file_name
        )

        SQLAlchemyDriver.setup_db = lambda _: None
        db = SQLAlchemyDriver(config["DB"])
        with db.session as session:
            clear_out_unused_filter_sets(session)
            session.commit()
        
        logger.info("Done, Job succefully completed.")
    
    except Exception as e:
        logger.error(f"Error while clearing out unused filter sets: {e}")
        exit(1)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])