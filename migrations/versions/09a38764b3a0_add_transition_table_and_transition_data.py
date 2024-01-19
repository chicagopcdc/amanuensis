"""add transition table and transition data

Revision ID: 09a38764b3a0
Revises: e2dde7e39938
Create Date: 2023-09-14 11:11:27.065014

"""
from alembic import op
import sqlalchemy as sa
from userportaldatamodel.models import State, Transition
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = '09a38764b3a0'
down_revision = 'e2dde7e39938'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'transition',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('state_src_id', sa.Integer(), nullable=False),
        sa.Column('state_dst_id', sa.Integer(), nullable=False),
        sa.Column('create_date', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('update_date', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['state_src_id'], ['state.id']),
        sa.ForeignKeyConstraint(['state_dst_id'], ['state.id']),
        sa.PrimaryKeyConstraint('id')
    )
    conn = op.get_bind()
    session = Session(bind=conn)
    transitions = []

    states = session.query(State.name, State.id).all()
    state_dict = {name: id for name, id in states}
   
    transitions.append(Transition(state_src_id=state_dict["Draft"], state_dst_id=state_dict["Submitted"]))
    transitions.append(Transition(state_src_id=state_dict["Draft"], state_dst_id=state_dict["Withdrawal"]))
    transitions.append(Transition(state_src_id=state_dict["Submitted"], state_dst_id=state_dict["In Review"]))
    transitions.append(Transition(state_src_id=state_dict["Submitted"], state_dst_id=state_dict["Withdrawal"]))
    transitions.append(Transition(state_src_id=state_dict["In Review"], state_dst_id=state_dict["Approved"]))
    transitions.append(Transition(state_src_id=state_dict["In Review"], state_dst_id=state_dict["Approved with Feedback"]))
    transitions.append(Transition(state_src_id=state_dict["In Review"], state_dst_id=state_dict["Revision"]))
    transitions.append(Transition(state_src_id=state_dict["In Review"], state_dst_id=state_dict["Withdrawal"]))
    transitions.append(Transition(state_src_id=state_dict["In Review"], state_dst_id=state_dict["Rejected"]))
    transitions.append(Transition(state_src_id=state_dict["Revision"], state_dst_id=state_dict["In Review"]))
    transitions.append(Transition(state_src_id=state_dict["Revision"], state_dst_id=state_dict["Withdrawal"]))
    transitions.append(Transition(state_src_id=state_dict["Approved"], state_dst_id=state_dict["Request Criteria Finalized"]))
    transitions.append(Transition(state_src_id=state_dict["Approved with Feedback"], state_dst_id=state_dict["Request Criteria Finalized"]))
    transitions.append(Transition(state_src_id=state_dict["Request Criteria Finalized"], state_dst_id=state_dict["Agreements Negotiation"]))
    transitions.append(Transition(state_src_id=state_dict["Agreements Negotiation"], state_dst_id=state_dict["Agreements Executed"]))
    transitions.append(Transition(state_src_id=state_dict["Agreements Executed"], state_dst_id=state_dict["Data Available"]))
    transitions.append(Transition(state_src_id=state_dict["Data Available"], state_dst_id=state_dict["Data Downloaded"]))
    transitions.append(Transition(state_src_id=state_dict["Data Downloaded"], state_dst_id=state_dict["Published"]))

    session.add_all(transitions)
    session.commit()


def downgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    session.query(Transition).delete()
    session.commit()
    op.drop_table('transition')
