import flask
import json
from cdislogging import get_logger

from amanuensis.resources.userdatamodel import (
    create_consortium,
    get_consotium_by_code,
    get_consortiums_by_code
)
from amanuensis.resources import filterset
from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden
from amanuensis.models import (
    ConsortiumDataContributor
)

from amanuensis.utils import get_consortium_list


logger = get_logger(__name__)


def create(logged_user_id, name, code):
    with flask.current_app.db.session as session:
        return create_consortium(session, code=code, name=name)

def get(code,session = None):
    if code is None:
        return None

    if session:
        return get_consotium_by_code(session, code=code)
    else:
        with flask.current_app.db.session as session:
            return get_consotium_by_code(session, code=code)

def get_consortiums_from_fitersets(filter_sets, session=None):
    if not filter_sets:
        return None
    
    consortiums_from_guppy = set()

    return_consortiums = {}

    #get consortiums in filter-sets from guppy
    for s in filter_sets:
        # Get a list of consortiums the cohort of data is from
        # example or retuned values - consoritums = ['INRG']
        # s.filter_object - you can use getattr to get the value or implement __getitem__ - https://stackoverflow.com/questions/11469025/how-to-implement-a-subscriptable-class-in-python-subscriptable-class-not-subsc
        consortiums_from_guppy.update(consortium.upper() for consortium in get_consortium_list(s.graphql_object, s.ids_list))  
    
    with session if session else flask.current_app.db.session as session:
        #find which consortiums already exist in DB
        present_consortiums = get_consortiums_by_code(session, consortiums_from_guppy)

        return_consortiums = {consortium.code: consortium for consortium in present_consortiums}

        #find which consortiums do not exist in DB
        new_consortiums = consortiums_from_guppy - return_consortiums.keys()

        #add consortiums to DB that are not present
        for code in new_consortiums:
            return_consortiums[code] = create_consortium(session, code, code)

    #return all consortiums from filter-sets
    # consortiums = {consortium_code: consortium_object}
    return return_consortiums


    

