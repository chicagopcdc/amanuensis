from amanuensis.errors import NotFound, UserError
from amanuensis.models import Search, FilterSourceType
import pytest
from amanuensis.resources.userdatamodel.search import create_filter_set, update_filter_set, get_filter_sets
from amanuensis.resources.userdatamodel.associated_users import create_associated_user


@pytest.fixture(scope="module", autouse=True)
def create_users(session, add_user_to_fence):
    user_id, user_email = add_user_to_fence(email=f"user_1@{__name__}.com", name=__name__)
    admin_id, admin_email = add_user_to_fence(email=f"admin@{__name__}.com", name=__name__, role="admin")

    user = create_associated_user(session, email=user_email, user_id=user_id)
    admin = create_associated_user(session,email=admin_email, user_id=admin_id)

    yield user, admin

@pytest.mark.order(1)
def test_create_search(session, create_users):

    user_filter_set = create_filter_set(
            session,
            explorer_id=1,
            logged_user_id=create_users[0].user_id,
            is_amanuensis_admin=False,
            name = f"{__name__}_user",
            description= "",
            filter_object= {"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
            ids_list=None,
            graphql_object={"AND":[{"IN":{"consortium":["INRG"]}},{"IN":{"sex":["Male"]}}]}
    )

    admin_filter_set = create_filter_set(
            session,
            explorer_id=1,
            logged_user_id=create_users[1].user_id,
            is_amanuensis_admin=True,
            name = f"{__name__}_admin",
            description= "",
            filter_object= {"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False},"sex":{"__type":"OPTION","selectedValues":["Male"],"isExclusion":False}}},
            ids_list=None,
            graphql_object={"AND":[{"IN":{"consortium":["INRG"]}},{"IN":{"sex":["Male"]}}]}
    )


    assert admin_filter_set.filter_source == FilterSourceType.manual
    assert user_filter_set.filter_source == FilterSourceType.explorer


def test_update_search(session, create_users):
    
    user_filter_set = get_filter_sets(
            session,
            user_id=create_users[0].user_id,
            many=False
    )


    update_search = update_filter_set(
            session,
            logged_user_id=create_users[0].user_id,
            filter_set_id=user_filter_set.id,
            explorer_id=1,
            name = f"{__name__}_user_updated",
    )

    updated_user_filter_set = get_filter_sets(
            session,
            user_id=create_users[0].user_id,
            many=False
    )


    assert updated_user_filter_set.name == f"{__name__}_user_updated"


def test_delete_search(session, create_users):

    user_filter_set = get_filter_sets(
            session,
            user_id=create_users[0].user_id,
            many=False
    )

    update_filter_set(
            session,
            logged_user_id=create_users[0].user_id,
            filter_set_id=user_filter_set.id,
            explorer_id=1,
            delete=True
    )

    with pytest.raises(NotFound):
        get_filter_sets(
                session,
                user_id=create_users[0].user_id,
                many=False,
                throw_not_found=True
        )