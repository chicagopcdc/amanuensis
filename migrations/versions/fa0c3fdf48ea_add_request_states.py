"""Add request states

Revision ID: fa0c3fdf48ea
Revises: f7ef7b53a36e
Create Date: 2022-12-12 19:23:41.792566

"""
import logging

from alembic import op
from sqlalchemy.orm import Session
from userportaldatamodel.models import State

# revision identifiers, used by Alembic.
revision = "fa0c3fdf48ea"
down_revision = "f7ef7b53a36e"
branch_labels = None
depends_on = None

logger = logging.getLogger("amanuensis.alembic")


def upgrade() -> None:

    states = []

    states.append(State(name="Draft", code="DRAFT"))

    states.append(State(name="Submitted", code="SUBMITTED"))

    states.append(State(name="Revision", code="REVISION"))

    states.append(State(name="Approved with Feedback", code="APPROVED_WITH_FEEDBACK"))

    states.append(
        State(name="Request Criteria Finalized", code="REQUEST_CRITERIA_FINALIZED")
    )

    states.append(State(name="Withdrawal", code="WITHDRAWAL"))

    states.append(
        State(
            name="Agreements Negotiation",
            code="AGREEMENTS_NEGOTIATION",
        )
    )

    states.append(State(name="Agreements Executed", code="AGREEMENTS_EXECUTED"))

    states.append(State(name="Data Available", code="DATA_AVAILABLE"))

    states.append(State(name="Data Downloaded", code="DATA_DOWNLOADED"))

    states.append(State(name="Published", code="PUBLISHED"))

    conn = op.get_bind()
    session = Session(bind=conn)
    session.add_all(states)
    session.commit()


def downgrade() -> None:

    state_codes = [
        "DRAFT",
        "SUBMITTED",
        "REVISION",
        "APPROVED_WITH_FEEDBACK",
        "REQUEST_CRITERIA_FINALIZED",
        "WITHDRAWAL",
        "AGREEMENTS_NEGOTIATION",
        "AGREEMENTS_EXECUTED",
        "DATA_AVAILABLE",
        "DATA_DOWNLOADED",
        "PUBLISHED",
    ]
    conn = op.get_bind()
    session = Session(bind=conn)
    for code in state_codes:
        session.query(State).filter(State.code == code).delete()
    session.commit()
