from alembic import context
import logging
from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool

from cdislogging import get_logger
from userportaldatamodel import Base
from sqlalchemy import text
from amanuensis.config import config as amanuensis_config
from amanuensis.settings import CONFIG_SEARCH_FOLDERS


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("amanuensis.alembic")

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

amanuensis_config.load(
    config_path=os.environ.get("DEFAULT_CFG_PATH"), 
    search_folders=CONFIG_SEARCH_FOLDERS,  # for deployments
)

config.set_main_option("sqlalchemy.url", str(amanuensis_config["DB"]))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            if connection.dialect.name == "postgresql":
                logger.info(
                    "Locking database to ensure only 1 migration runs at a time"
                )
                # This prevents 2 amanuensis instances from trying to migrate the same
                # DB at the same time, but does not prevent a job (such as
                # usersync) from updating the DB while a migration is running.
                # Solution based on https://github.com/sqlalchemy/alembic/issues/633
                # TODO lock the DB for all processes during migrations
                connection.execute(
                    text(f"SELECT pg_advisory_xact_lock({amanuensis_config['DB_MIGRATION_POSTGRES_LOCK_KEY']});")

                )
            context.run_migrations()
            if connection.dialect.name == "postgresql":
                # The lock is released when the transaction ends.
                logger.info("Releasing database lock")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
