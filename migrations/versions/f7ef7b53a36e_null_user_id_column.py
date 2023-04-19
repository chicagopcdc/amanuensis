"""add_save

Revision ID: f7ef7b53a36e
Revises: 04feb6aab17b
Create Date: 2022-12-01 13:57:07.441613

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7ef7b53a36e'
down_revision = 'b1c926c2d318'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("search_is_shared", "user_id", nullable=True)


def downgrade() -> None:
    op.alter_column("search_is_shared", "user_id", nullable=False)
