
from cdislogging import get_logger
from userportaldatamodel.driver import SQLAlchemyDriver
from amanuensis.models import Search, ProjectSearch, SearchIsShared
from amanuensis.settings import CONFIG_SEARCH_FOLDERS
from amanuensis.config import config
from sqlalchemy import and_, not_, exists
logger = get_logger(__name__, log_level="info")



def main():
    config.load(
        search_folders=CONFIG_SEARCH_FOLDERS
    )
    SQLAlchemyDriver.setup_db = lambda _: None
    db = SQLAlchemyDriver(config["DB"])
    with db.session as session:
        query = (
        session.query(Search)
            .filter(
                Search.user_id.is_(None),  # user_id is NULL
                ~session.query(ProjectSearch)
                .filter(ProjectSearch.search_id == Search.id)
                .exists(),  # id not in project_has_search
                ~session.query(SearchIsShared)
                .filter(SearchIsShared.search_id == Search.id)
                .exists(),  # id not in search_is_shared
            )
        )

        # Execute the query
        for result in query.all():
            logger.info(f"Deleting search {result.id} {result.name}")
        query.delete()
        session.commit()
        logger.info("Done, Job succefully completed.")

if __name__ == "__main__":
    main()
