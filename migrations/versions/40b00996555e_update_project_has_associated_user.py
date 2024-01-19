"""update project_has_associated_user

Revision ID: 40b00996555e
Revises: 72936c3fdac6
Create Date: 2023-11-03 11:10:23.808252

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import logging
from userportaldatamodel.models import *
from sqlalchemy.orm import Session
# revision identifiers, used by Alembic.
revision = '40b00996555e'
down_revision = '72936c3fdac6'
branch_labels = None
depends_on = None

logger = logging.getLogger("amanuensis.alembic")

def upgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    role_ids_role_codes = session.query(AssociatedUserRoles.id, AssociatedUserRoles.code).all()
    roles_dict = {}
    for role in role_ids_role_codes:
        roles_dict[role.code] = role.id

    logger.warn("userporataldatamodel must be at version 1.6.0 or greater")
    op.add_column("project_has_associated_user", sa.Column('role_id', sa.Integer, sa.ForeignKey('associated_user_roles.id')))

    op.execute(f"UPDATE project_has_associated_user SET role_id = CASE WHEN role = 'DATA_ACCESS' THEN {roles_dict['DATA_ACCESS']} WHEN role = 'METADATA_ACCESS' THEN {roles_dict['METADATA_ACCESS']} ELSE {roles_dict['METADATA_ACCESS']} END")

    op.drop_column("project_has_associated_user", 'role')

def downgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    role_ids_role_codes = session.query(AssociatedUserRoles.id, AssociatedUserRoles.code).all()
    roles_dict = {}
    for role in role_ids_role_codes:
        roles_dict[role.code] = role.id
    logger.warn("userportaldatamodel must be at version 1.5.0 or less")
    op.add_column("project_has_associated_user", sa.Column('role', sa.String, nullable=False, server_default="METADATA_ACESS"))

    op.execute(f"UPDATE project_has_associated_user SET role = CASE WHEN role_id  = {roles_dict['DATA_ACCESS']} THEN 'DATA_ACCESS' WHEN role_id  = {roles_dict['METADATA_ACCESS']} THEN 'METADATA_ACCESS' ELSE 'METADATA_ACCESS' END")

    op.drop_column("project_has_associated_user", 'role_id')
