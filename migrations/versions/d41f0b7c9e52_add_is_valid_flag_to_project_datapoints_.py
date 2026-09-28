"""add_is_valid_flag_to_project_datapoints_table

Revision ID: d41f0b7c9e52
Revises: b5a7ca32c5b1
Create Date: 2026-08-25 13:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd41f0b7c9e52'
down_revision = 'b5a7ca32c5b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('project_datapoints', sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:

    op.drop_column('project_datapoints', 'is_valid')
