"""add_is_valid_flag_to_search_table

Revision ID: bfd4b47dd236
Revises: 57ef835d5488
Create Date: 2024-12-10 13:53:33.483734

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bfd4b47dd236'
down_revision = '57ef835d5488'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('search', sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    
    op.drop_column('search', 'is_valid')