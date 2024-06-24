"""require value for role

Revision ID: 57bc0c5a9733
Revises: 40b00996555e
Create Date: 2024-01-31 14:09:20.480237

"""
from alembic import op
from userportaldatamodel.models import AssociatedUserRoles
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = '57bc0c5a9733'
down_revision = '40b00996555e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    
    meta_data_role = session.query(AssociatedUserRoles.id).filter(AssociatedUserRoles.code == "METADATA_ACCESS").first()[0]
    
    op.execute(f"UPDATE project_has_associated_user SET role_id = {meta_data_role} WHERE role_id IS NULL")

    op.alter_column('project_has_associated_user', 'role_id', nullable=False)

def downgrade() -> None:
    op.alter_column('project_has_associated_user', 'role_id', nullable=True)
