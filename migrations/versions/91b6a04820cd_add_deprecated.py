"""add_deprecated

Revision ID: 91b6a04820cd
Revises: 57bc0c5a9733
Create Date: 2024-03-04 17:29:29.400433

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.session import Session
from userportaldatamodel.models import State

# revision identifiers, used by Alembic.
revision = '91b6a04820cd'
down_revision = '57bc0c5a9733'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    
    deprecated = State(name="DEPRECATED", code="DEPRECATED")

    session.add(deprecated)

    session.commit()


def downgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    session.query(State).filter(State.code == "DEPRECATED").delete()
    session.commit()
