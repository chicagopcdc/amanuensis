"""
Define sqlalchemy models.
The models here inherit from the `Base` in userportaldatamodel, so when the amanuensis app
is initialized, the resulting db session includes everything from userportaldatamodel
and this file.
The `migrate` function in this file is called every init and can be used for
database migrations.
"""
import warnings
from enum import Enum

import bcrypt
import flask
# from authlib.flask.oauth2.sqla import (OAuth2AuthorizationCodeMixin,
#                                        OAuth2ClientMixin)
from sqlalchemy import (BigInteger, Boolean, Column, DateTime, Integer,
                        MetaData, String, Table, Text)
from sqlalchemy import exc as sa_exc
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func
from userportaldatamodel import Base
from userportaldatamodel.models import (AttributeList, AttributeListValue,
                                        Attributes, ConsortiumDataContributor,
                                        InputType, Message, Project, Receiver,
                                        Request, Search, FilterSourceType, State, AssociatedUser, ProjectAssociatedUser, AssociatedUserRoles, RequestState, SearchIsShared)



from amanuensis.config import config



##### DEPRECATED ######
to_timestamp = (
    "CREATE OR REPLACE FUNCTION pc_datetime_to_timestamp(datetoconvert timestamp) "
    "RETURNS BIGINT AS "
    "$BODY$ "
    "select extract(epoch from $1)::BIGINT "
    "$BODY$ "
    "LANGUAGE 'sql' IMMUTABLE STRICT;"
)


def migrate(driver):
    if not driver.engine.dialect.supports_alter:
        print(
            "This engine dialect doesn't support altering so we are not migrating even if necessary!"
        )
        return

    md = MetaData()


    states =  []
    states.append(
            State(
                name="In Review",
                code= "IN_REVIEW"
                )
        )
    states.append(
            State(
                name="Rejected",
                code= "REJECTED"
                )
        )
    states.append(
            State(
                name="Approved",
                code= "APPROVED"
                )
        )
    states.append(
            State(
                name="Data Delivered",
                code= "DATA_DELIVERED"
                )
        )

    consortiums = []
    consortiums.append(
            ConsortiumDataContributor(
                name="INRG", 
                code ="INRG"
                )
        )
    consortiums.append(
            ConsortiumDataContributor(
                name="INSTRUCT", 
                code ="INSTRUCT"
                )
        )


    with driver.session as session:
        db_states = session.query(State).all()
        db_codes = [db_state.code for db_state in db_states]
        states = list(filter(lambda x: x.code not in db_codes, states))
        session.bulk_save_objects(states)

        db_consortiums = session.query(ConsortiumDataContributor).all()
        db_consortium_codes = [db_consortium.code for db_consortium in db_consortiums]
        consortiums = list(filter(lambda x: x.code not in db_consortium_codes, consortiums))
        session.bulk_save_objects(consortiums)



def add_foreign_key_column_if_not_exist(
    table_name,
    column_name,
    column_type,
    fk_table_name,
    fk_column_name,
    driver,
    metadata,
):
    column = Column(column_name, column_type)
    add_column_if_not_exist(table_name, column, driver, metadata)
    add_foreign_key_constraint_if_not_exist(
        table_name, column_name, fk_table_name, fk_column_name, driver, metadata
    )


def drop_foreign_key_column_if_exist(table_name, column_name, driver, metadata):
    drop_foreign_key_constraint_if_exist(table_name, column_name, driver, metadata)
    drop_column_if_exist(table_name, column_name, driver, metadata)


def add_column_if_not_exist(table_name, column, driver, metadata, default=None):
    column_name = column.compile(dialect=driver.engine.dialect)
    column_type = column.type.compile(driver.engine.dialect)

    table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)
    if str(column_name) not in table.c:
        with driver.session as session:
            command = 'ALTER TABLE "{}" ADD COLUMN {} {}'.format(
                table_name, column_name, column_type
            )
            if not column.nullable:
                command += " NOT NULL"
            if getattr(column, "default"):
                default = column.default.arg
                if isinstance(default, str):
                    default = "'{}'".format(default)
                command += " DEFAULT {}".format(default)
            command += ";"

            session.execute(command)
            session.commit()


def drop_column_if_exist(table_name, column_name, driver, metadata):
    table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)
    if column_name in table.c:
        with driver.session as session:
            session.execute(
                'ALTER TABLE "{}" DROP COLUMN {};'.format(table_name, column_name)
            )
            session.commit()


def add_foreign_key_constraint_if_not_exist(
    table_name, column_name, fk_table_name, fk_column_name, driver, metadata
):
    table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)
    foreign_key_name = "{}_{}_fkey".format(table_name.lower(), column_name)

    if column_name in table.c:
        foreign_keys = [fk.name for fk in getattr(table.c, column_name).foreign_keys]
        if foreign_key_name not in foreign_keys:
            with driver.session as session:
                session.execute(
                    'ALTER TABLE "{}" ADD CONSTRAINT {} '
                    'FOREIGN KEY({}) REFERENCES "{}" ({});'.format(
                        table_name,
                        foreign_key_name,
                        column_name,
                        fk_table_name,
                        fk_column_name,
                    )
                )
                session.commit()


def set_foreign_key_constraint_on_delete_cascade(
    table_name, column_name, fk_table_name, fk_column_name, driver, session, metadata
):
    set_foreign_key_constraint_on_delete(
        table_name,
        column_name,
        fk_table_name,
        fk_column_name,
        "CASCADE",
        driver,
        session,
        metadata,
    )


def set_foreign_key_constraint_on_delete_setnull(
    table_name, column_name, fk_table_name, fk_column_name, driver, session, metadata
):
    set_foreign_key_constraint_on_delete(
        table_name,
        column_name,
        fk_table_name,
        fk_column_name,
        "SET NULL",
        driver,
        session,
        metadata,
    )


def set_foreign_key_constraint_on_delete(
    table_name,
    column_name,
    fk_table_name,
    fk_column_name,
    ondelete,
    driver,
    session,
    metadata,
):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Predicate of partial index \S+ ignored during reflection",
            category=sa_exc.SAWarning,
        )
        table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)
    foreign_key_name = "{}_{}_fkey".format(table_name.lower(), column_name)

    if column_name in table.c:
        session.execute(
            'ALTER TABLE ONLY "{}" DROP CONSTRAINT IF EXISTS {}, '
            'ADD CONSTRAINT {} FOREIGN KEY ({}) REFERENCES "{}" ({}) ON DELETE {};'.format(
                table_name,
                foreign_key_name,
                foreign_key_name,
                column_name,
                fk_table_name,
                fk_column_name,
                ondelete,
            )
        )


def drop_foreign_key_constraint_if_exist(table_name, column_name, driver, metadata):
    table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)
    foreign_key_name = "{}_{}_fkey".format(table_name.lower(), column_name)

    if column_name in table.c:
        foreign_keys = [fk.name for fk in getattr(table.c, column_name).foreign_keys]
        if foreign_key_name in foreign_keys:
            with driver.session as session:
                session.execute(
                    'ALTER TABLE "{}" DROP CONSTRAINT {};'.format(
                        table_name, foreign_key_name
                    )
                )
                session.commit()


def add_unique_constraint_if_not_exist(table_name, column_name, driver, metadata):
    table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)
    index_name = "{}_{}_key".format(table_name, column_name)

    if column_name in table.c:
        indexes = [index.name for index in table.indexes]

        if index_name not in indexes:
            with driver.session as session:
                session.execute(
                    'ALTER TABLE "{}" ADD CONSTRAINT {} UNIQUE ({});'.format(
                        table_name, index_name, column_name
                    )
                )
                session.commit()


def drop_unique_constraint_if_exist(table_name, column_name, driver, metadata):
    table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)
    constraint_name = "{}_{}_key".format(table_name, column_name)

    if column_name in table.c:
        constraints = [
            constaint.name for constaint in getattr(table.c, column_name).constraints
        ]

        unique_index = None
        for index in table.indexes:
            if index.name == constraint_name:
                unique_index = index

        if constraint_name in constraints or unique_index:
            with driver.session as session:
                session.execute(
                    'ALTER TABLE "{}" DROP CONSTRAINT {};'.format(
                        table_name, constraint_name
                    )
                )
                session.commit()


def drop_default_value(table_name, column_name, driver, metadata):
    table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)

    if column_name in table.c:
        with driver.session as session:
            session.execute(
                'ALTER TABLE "{}" ALTER COLUMN "{}" DROP DEFAULT;'.format(
                    table_name, column_name
                )
            )
            session.commit()


def add_not_null_constraint(table_name, column_name, driver, metadata):
    table = Table(table_name, metadata, autoload=True, autoload_with=driver.engine)

    if column_name in table.c:
        with driver.session as session:
            session.execute(
                'ALTER TABLE "{}" ALTER COLUMN "{}" SET NOT NULL;'.format(
                    table_name, column_name
                )
            )
            session.commit()

##### END DEPRECATED ######
