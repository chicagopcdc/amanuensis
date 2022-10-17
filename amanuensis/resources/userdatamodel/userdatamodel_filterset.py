from secrets import token_urlsafe
import uuid
# from sqlalchemy import func

from amanuensis.errors import NotFound
from amanuensis.models import Search, FilterSourceType, SearchIsShared

__all__ = [
    "get_filter_sets",
    "get_filter_sets_by_user_id",
    "create_filter_set",
    "delete_filter_set",
    "update_filter_set",
    # "get_filter_sets_by_name",
    "create_filter_set_snapshot",
    "get_snapshot_by_token",
]


def get_filter_sets(
    current_session, logged_user_id, is_amanuensis_admin, filter_set_ids, explorer_id
):
    """
    Returns all, one, or multiple by id
    filter_set_id may be id(int), ids(array), or None
    """
    # TODO make class Search serializable
    query = current_session.query(Search).filter(
        Search.active == True, Search.user_id == logged_user_id
    )

    if not is_amanuensis_admin:
        query = query.filter(
            Search.filter_source_internal_id == explorer_id,
            Search.filter_source == FilterSourceType.explorer,
        )

    if filter_set_ids:
        if not isinstance(filter_set_ids, list):
            filter_set_ids = [filter_set_ids]
        query = query.filter(Search.id.in_(filter_set_ids))

    return query.all()

# def get_filter_sets_by_name(current_session, user_id, is_amanuensis_admin, names, explorer_id):
#     '''
#     Returns all, one, or multiple by id
#     filter_set_id may be id(int), ids(array), or None
#     '''
#     #TODO make class Search serializable
#     query = current_session.query(Search).filter(
#         Search.active == True, 
#         Search.user_id == user_id
#     )

#     if is_amanuensis_admin:
#         query = query.filter(Search.filter_source == FilterSourceType.manual)
#     else:
#         query = query.filter(
#             Search.filter_source_internal_id == explorer_id,
#             Search.filter_source == FilterSourceType.explorer
#         )   

#     if names:
#         if not isinstance(names, list):
#             names = [names]
#         query = query.filter(Search.name.in_(names))

#     return query.all()


def get_filter_sets_by_user_id(session, user_id, is_admin):
    query = session.query(Search).filter(
        Search.active == True, 
        Search.user_id == user_id
    )

    if not is_admin:
        query = query.filter(
            Search.filter_source == FilterSourceType.explorer
        )   

    return query.all()


def create_filter_set(current_session, logged_user_id, is_amanuensis_admin, explorer_id, name, description, filter_object, ids_list, graphql_object):
    new_filter_set = Search(
        user_id=logged_user_id,
        filter_source_internal_id=explorer_id,
        filter_source=FilterSourceType.manual if is_amanuensis_admin else FilterSourceType.explorer,
        user_source="fence",
        name=name,
        description=description,
        filter_object=filter_object,
        ids_list=ids_list,
        graphql_object=graphql_object
    )
    # TODO add es_index, add dataset_version
    current_session.add(new_filter_set)
    current_session.flush()

    if is_amanuensis_admin:
        return {
            "name": new_filter_set.name,
            "id": new_filter_set.id,
            "filter_source": new_filter_set.filter_source,
            "description": new_filter_set.description, 
            "ids_list": new_filter_set.ids_list,
            "graphql_object": new_filter_set.graphql_object
        }
    else: 
        return {
            "name": new_filter_set.name, 
            "id": new_filter_set.id,
            "explorer_id": new_filter_set.filter_source_internal_id,
            "description": new_filter_set.description, 
            "filters": new_filter_set.filter_object
        }


def update_filter_set(current_session, logged_user_id, filter_set_id, explorer_id, name, description, filter_object, graphql_object):
    data = {}
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    if filter_object:
        data['filter_object'] = filter_object
    if graphql_object:
        data["graphql_object"] = graphql_object

    # TODO check that at least one has changed
    num_updated = (
        current_session.query(Search)
        .filter(
            Search.id == filter_set_id,
            Search.filter_source_internal_id == explorer_id,
            Search.filter_source == FilterSourceType.explorer,
            Search.user_id == logged_user_id,
        )
        .update(data)
    )
    if num_updated > 0:
        return {
            "code": 200,
            "updated": int(filter_set_id),
            "explorer_id": int(explorer_id),
        }

    return {
        "code": 500,
        "error": "Nothing has been updated, check the logs to see what happened during the transaction.",
    }


def delete_filter_set(current_session, logged_user_id, filter_set_id, explorer_id):
    """
    Delete the filter_set from the database.
    The filter_set has to be assigned to 0 project request
    """
    filter_set = (
        current_session.query(Search)
        .filter(
            Search.id == filter_set_id,
            Search.filter_source_internal_id == explorer_id,
            Search.filter_source == FilterSourceType.explorer,
            Search.user_id == logged_user_id,
        )
        .first()
    )

    if not filter_set:
        return {"code": 404, "result": "error, filter_set not found"}

    # TODO
    # proj_request = (
    #     current_session.query(ProjectToBucket)
    #     .filter(ProjectToBucket.project_id == proj.id)
    #     .first()
    # )

    # if proj_request:
    #     msg = (
    #         "error, project still has buckets associated with it. Please"
    #         " remove those first and then retry."
    #     )
    #     return {"result": msg}

    # current_session.delete(filter_set)
    filter_set.active = False
    return {
        "code": 200,
        "deleted": filter_set.id,
        "explorer_id": filter_set.filter_source_internal_id,
    }


def share_filter_set(
    current_session,
    users,
    filter_set_id,
    access_role="READ"
):
    """
    Share the filter set with another user.
    """  
    if not filter_set_id:
        raise NotFound("error, filter_set not found")


    shareable_token = None
    token_generated = False
    while not token_generated:
        shareable_token = str(uuid.uuid4())

        snapshot = current_session.query(SearchIsShared)
            .filter(SearchIsShared.shareable_token == shareable_token)
            .first()

        if not snapshot:
            token_generated = True

    shared_search = SearchIsShared(
        search_id=filter_set_id,
        user_id=users,
        access_role=access_role,
        shareable_token=shareable_token
    )

    # filter_set.snapshots.append(shared_search)
    current_session.add(shared_search)
    current_session.flush()

    return shareable_token


def create_filter_set_snapshot(current_session, logged_user_id, filter_set_id, users_list):
    """
    Create a new snapshot of the filter_set.
    """
    logged_user_id = int(logged_user_id)

    filter_set = (
        current_session.query(Search).filter(Search.id == filter_set_id, Search.user_id == logged_user_id).first()
    )

    if not filter_set:
        raise NotFound("error, filter_set not found")


    #Create a new search linked to no user since this will just be a snapshot in time and no user should be able to edit it.
    snapshot = create_filter_set(
        current_session,
        None,
        False,
        filter_set.filter_source_internal_id,
        filter_set.name,
        filter_set.description,
        filter_set.filter_object,
        filter_set.ids_list,
        filter_set.graphql_object
    )

    shared_token = share_filter_set(
        current_session,
        users_list,
        snapshot["id"],
        "READ"
    )

    return shared_token

def get_snapshot_by_token(session, logged_user_id, token):
    """
    Get the snapshot by the token.
    """
    logged_user_id = int(logged_user_id)

    snapshot = (
        session.query(SearchIsShared)
        .filter(SearchIsShared.shareable_token == token)
        .first()
    )

    if not snapshot:
        raise NotFound("error, snapshot not found") 

    return {
            "id": snapshot.search_id,
            "name": snapshot.search.name,
            "explorer_id": snapshot.search.filter_source_internal_id,
            "description": snapshot.search.description,
            "filters": snapshot.search.filter_object
        }

