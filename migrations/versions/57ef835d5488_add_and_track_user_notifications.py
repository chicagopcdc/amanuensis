"""add_and_track_user_messages

Revision ID: 57ef835d5488
Revises: 91b6a04820cd
Create Date: 2024-07-17 21:42:48.531346

"""
from alembic import op
import sqlalchemy as sa
from userportaldatamodel.models import Notification, NotificationLog

# revision identifiers, used by Alembic.
revision = '57ef835d5488'
down_revision = '91b6a04820cd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    
    op.create_table('notification_log', 
                    sa.Column('id', sa.Integer(), nullable = False, autoincrement=True), 
                    sa.Column('message', sa.String(), nullable = False), 
                    sa.Column('create_date', sa.DateTime(), nullable = False, server_default = sa.text('NOW()')),
                    sa.Column('active', sa.Boolean(), nullable=True, default=True),  
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('message')
    )

    op.create_table('notification', 
                    sa.Column('notification_log_id', sa.Integer(), sa.ForeignKey("notification_log.id"), nullable = False), 
                    sa.Column('user_id', sa.Integer(), nullable = False), 
                    sa.Column("seen", sa.Boolean(), nullable=True, default=False),
                    sa.Column('create_date', sa.DateTime(), nullable = False, server_default = sa.text('NOW()')),
                    sa.PrimaryKeyConstraint('user_id', 'notification_log_id')
    )


def downgrade() -> None:
    op.drop_table('notification')
    op.drop_table('notification_log')
    
    
