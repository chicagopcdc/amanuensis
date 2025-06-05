"""convert_json_null_to_empty_objects

Revision ID: c6059263d6b9
Revises: bfd4b47dd236
Create Date: 2025-05-21 17:24:11.244001

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = 'c6059263d6b9'
down_revision = 'bfd4b47dd236'
branch_labels = None
depends_on = None


def upgrade() -> None:
        # Use raw SQL to update records where filter_object is JSON null (not SQL NULL)
    op.execute(
        text("""
        UPDATE search 
        SET filter_object = '{}'::jsonb 
        WHERE filter_object = 'null'::jsonb;
        """)
    )

    op.execute(
        text("""
        UPDATE search 
        SET graphql_object = '{}'::jsonb 
        WHERE graphql_object = 'null'::jsonb;
        """)
    )
    
    


def downgrade() -> None:
    pass
