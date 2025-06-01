"""adding_datapoints_table

Revision ID: ec9c951d51ca
Revises: bfd4b47dd236
Create Date: 2025-05-19 15:26:49.645467

"""
from alembic import op
import sqlalchemy as sa
#from userportaldatamodel.models import AssociatedUserRoles
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session
from sqlalchemy.schema import ForeignKey
from userportaldatamodel.models import AssociatedUserRoles

# revision identifiers, used by Alembic.
revision = 'ec9c951d51ca'
down_revision = 'bfd4b47dd236'
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "project_datapoints",
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('term', sa.String, nullable=False),
        sa.Column('value_list', ARRAY(sa.String()), nullable=False, default=list),
        sa.Column('type', sa.CHAR(),nullable=False),

        sa.Column('project_id', sa.Integer(),ForeignKey("project.id"),nullable=True),


        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("type IN ('w', 'b')", name="type_check")
    )

    conn = op.get_bind()
    session = Session(bind=conn)

    roles = []
    roles.append(AssociatedUserRoles(role="DATA_ACCESS",code="DATA_ACCESS"))
    roles.append(AssociatedUserRoles(role="METADATA_ACCESS",code="METADATA_ACCESS"))
    session.add_all(roles)
    session.commit()



def downgrade() -> None:
    op.drop_table("project_datapoints")
    
