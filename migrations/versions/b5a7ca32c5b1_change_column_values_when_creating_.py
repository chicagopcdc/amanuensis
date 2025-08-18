"""change column values when creating associated users who haven't signed up

Revision ID: b5a7ca32c5b1
Revises: ec9c951d51ca
Create Date: 2025-08-10 20:17:50.577021

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5a7ca32c5b1'
down_revision = 'ec9c951d51ca'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE associated_user
        SET active = False, user_source = NULL
        WHERE user_id IS NULL;
    """)


def downgrade() -> None:
    pass
