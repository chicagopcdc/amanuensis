"""change column values when creating associated users who haven't signed up

Revision ID: b5a7ca32c5b1
Revises: ec9c951d51ca
Create Date: 2025-08-10 20:17:50.577021

"""
from alembic import op
from sqlalchemy.orm.session import Session
from userportaldatamodel.models import AssociatedUser


# revision identifiers, used by Alembic.
revision = 'b5a7ca32c5b1'
down_revision = 'ec9c951d51ca'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    session.query(AssociatedUser).filter(AssociatedUser.user_id == None).update({"active": False, "user_source": None})
    session.commit()

def downgrade() -> None:
    pass
