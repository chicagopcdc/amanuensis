
from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    ConsortiumDataContributor
)
from cdislogging import get_logger
logger = get_logger(__name__)
__all__ = [
    "create_consortium",
    "get_consortiums"
]

def get_consortiums(current_session, 
                    id=None, 
                    name=None, 
                    code=None,  
                    throw_not_found=False, 
                    many=True):
    
    logger.info(f"get_consortiums: {locals()}")

    consortiums = current_session.query(ConsortiumDataContributor)

    if id is not None:
        id = [id] if not isinstance(id, list) else id
        consortiums = consortiums.filter(ConsortiumDataContributor.id.in_(id))
    
    if name:
        name = [name] if not isinstance(name, list) else name
        consortiums = consortiums.filter(ConsortiumDataContributor.name.in_(name))

    if code:
        code = [code] if not isinstance(code, list) else code
        consortiums = consortiums.filter(ConsortiumDataContributor.code.in_(code))

    consortiums = consortiums.all()

    if throw_not_found and not consortiums:
        raise NotFound(f"No consortiums found")

    if not many:
        if len(consortiums) > 1:
            raise UserError("More than one consortium found check inputs")
        else:
            consortiums = consortiums[0] if consortiums else None
    
    return consortiums


def create_consortium(current_session, name, code):

    consortium = get_consortiums(current_session, code=code, many=False)

    if consortium:
        logger.info(f"Consortium {code} already exists, skipping")
    
    else:
        consortium = ConsortiumDataContributor(
                        name=name,
                        code=code
                    )
        
        current_session.add(
            consortium
        )

    current_session.flush()

    return consortium

