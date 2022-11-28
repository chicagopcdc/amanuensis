"""Add search snapshot

Revision ID: b1c926c2d318
Revises: b506b97bbfce
Create Date: 2022-08-12 19:25:41.315459

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision = "b1c926c2d318"
down_revision = "b506b97bbfce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_is_shared",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("search_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.ARRAY(sa.Text()), nullable=False),
        sa.Column("access_role", sa.String(length=255), default="READ"),
        sa.Column("shareable_token", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["search_id"],
            ["search.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("search_is_shared")

