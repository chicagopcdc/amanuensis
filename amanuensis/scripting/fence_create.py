import os
import os.path
import time
from yaml import safe_load
import json
import pprint

from alembic.config import main as alembic_main
from cdislogging import get_logger
from sqlalchemy import func

from userportaldatamodel.driver import SQLAlchemyDriver

from amanuensis.models import (
    migrate,
)

from amanuensis.config import config


logger = get_logger(__name__)



# def notify_problem_users(db, emails, auth_ids, check_linking, google_project_id):
#     """
#     Builds a list of users (from provided list of emails) who do not
#     have access to any subset of provided auth_ids. Send email to users
#     informing them to get access to needed projects.

#     db (string): database instance
#     emails (list(string)): list of emails to check for access
#     auth_ids (list(string)): list of project auth_ids to check that emails have access
#     check_linking (bool): flag for if emails should be checked for linked google email
#     """
#     email_users_without_access(db, auth_ids, emails, check_linking, google_project_id)


def migrate_database():
    alembic_main(["--raiseerr", "upgrade", "head"])
    logger.info("Done.")



def main():
    # args = parse_arguments()
    # # get database information
    # sys.path.append(args.path)
    # if args.action == "migrate":
    #     migrate_database()
    migrate_database()
    


if __name__ == "__main__":
    main()
