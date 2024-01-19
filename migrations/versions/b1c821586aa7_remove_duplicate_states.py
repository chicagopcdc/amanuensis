"""remove_duplicate_states

Revision ID: b1c821586aa7
Revises: fa0c3fdf48ea
Create Date: 2023-06-08 17:27:11.052974

"""
from alembic import op
from sqlalchemy.orm.session import Session
from userportaldatamodel.models import State


# revision identifiers, used by Alembic.
revision = 'b1c821586aa7'
down_revision = 'fa0c3fdf48ea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    session.query(State).filter(State.code == "DATA_AVAILABLE").delete()
    session.query(State).filter(State.code == "DATA_DELIVERED").update({State.code: "DATA_AVAILABLE", State.name: "Data Available"})

    session.commit()


def downgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    session.query(State).filter(State.code == "DATA_AVAILABLE").update({State.code: "DATA_DELIVERED", State.name: "Data Delivered"})

    session.commit()


