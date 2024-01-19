"""add_interact

Revision ID: e2dde7e39938
Revises: b1c821586aa7
Create Date: 2023-06-28 15:32:23.306113

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from userportaldatamodel.models import ConsortiumDataContributor


# revision identifiers, used by Alembic.
revision = 'e2dde7e39938'
down_revision = 'b1c821586aa7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)

    consortiums = []
    consortiums.append(
            ConsortiumDataContributor(
                name="INTERACT", 
                code ="INTERACT"
                )
        )

    session.add_all(consortiums)
    session.commit()


def downgrade() -> None:
    consortium_codes = [
        "INTERACT"
    ]
    conn = op.get_bind()
    session = Session(bind=conn)
    for code in consortium_codes:
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == code).delete()
    session.commit()
