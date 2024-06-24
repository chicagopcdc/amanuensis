from cdislogging import get_logger
from amanuensis.resources.userdatamodel import get_all_associated_user_roles, get_associated_user_role_by_code
from amanuensis.models import AssociatedUserRoles
from amanuensis.errors import NotFound
import pytest

logger = get_logger(logger_name=__name__, log_level='debug')


def test_get_all_associated_user_roles(session):
    test_data = session.query(AssociatedUserRoles).all()
    data = get_all_associated_user_roles(session)
    assert data == test_data

def test_get_associated_user_role_by_code(session, roles):
    #test correct data
    data = get_associated_user_role_by_code("METADATA_ACCESS", current_session=session)
    assert data.code == "METADATA_ACCESS"
    #test no data
    data = get_associated_user_role_by_code("METADATA_ACCESS")
    assert data.code == "METADATA_ACCESS"
    data = get_associated_user_role_by_code(roles[0].code, current_session=session)
    assert data.id == roles[0].id
    #test incorrect data
    with pytest.raises(NotFound) as e:
        get_associated_user_role_by_code("NOTREALCODE", current_session=session)

    #tests incorrect data with no error
    data = get_associated_user_role_by_code("NOTREALCODE", current_session=session, throw_error=False)
    assert data == None