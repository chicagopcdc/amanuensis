from sqlalchemy import func

from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    ConsortiumDataContributor
)

__all__ = [
    "create_consortium",
    "get_consotium_by_code",
]


#TODO
#get_consortium_by_code has no error catch so errors are raised in the blueprints which creates redundent code
#clean up imports

def create_consortium(current_session, code, name):
    """
    Creates a consortium
    """
    new_consortium = ConsortiumDataContributor(code=code, name=name)

    current_session.add(new_consortium)
    # current_session.flush()
    current_session.commit()
    
    return new_consortium


def get_consotium_by_code(current_session, code):
    return current_session.query(ConsortiumDataContributor).filter_by(code=code).first()



