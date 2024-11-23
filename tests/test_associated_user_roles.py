import pytest
from amanuensis.resources.userdatamodel.associated_user_roles import get_associated_user_roles
from amanuensis.errors import NotFound, UserError

def test_get_associated_user_role_by_code(session):
    # Assuming the session contains a role with code 'MOD'
    role = get_associated_user_roles(session, code="DATA_ACCESS", many=False)
    assert role.code == "DATA_ACCESS"
    assert role.role == "DATA_ACCESS"

def test_get_assoicated_user_role_many(session):
    role = get_associated_user_roles(session, code=["DATA_ACCESS", "METADATA_ACCESS"])

    assert len(role) == 2

def test_get_associated_user_role_by_id(session):
    # Assuming the session contains a role with id 1
    role = get_associated_user_roles(session, id=1, many=False)
    assert role.id == 1
    assert role.role == "DATA_ACCESS"  # Assuming id=1 corresponds to "admin"

def test_no_roles_found_raises_error(session):
    with pytest.raises(NotFound):
        get_associated_user_roles(session, id=999, throw_not_found=True)

def test_no_roles_found_returns_empty_list(session):
    roles = get_associated_user_roles(session, id=999, throw_not_found=False)
    assert roles == []  # Expecting an empty list when no roles are found

def test_user_error(session):
    with pytest.raises(UserError):
        get_associated_user_roles(session, id=[1, 2], many=False)