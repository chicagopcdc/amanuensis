from amanuensis.models import SearchIsShared
import uuid
from amanuensis.errors import NotFound
from amanuensis.resources.userdatamodel.search import create_filter_set, get_filter_sets

__all__ = [
]

def get_shared_filter_sets(current_session, token):

    snapshot = current_session.query(SearchIsShared) \
                              .filter(SearchIsShared.shareable_token == token) \
                              .first()
    if not snapshot:
        raise NotFound("error, snapshot not found") 

    return snapshot



def create_filter_set_snapshot(current_session, 
                               logged_user_id, 
                               filter_set_id, 
                               users_list):
    """
    Create a new snapshot of the filter_set.
    """

    filter_set = get_filter_sets(
        current_session, 
        user_id=logged_user_id, 
        id=filter_set_id, 
        filter_by_source_type=False, 
        throw_not_found=True, 
        many=False
    )


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

    shareable_token = str(uuid.uuid4())

    shared_search = SearchIsShared(
        search_id=filter_set_id,
        user_id=users_list,
        access_role="READ",
        shareable_token=shareable_token
    )

    # filter_set.snapshots.append(shared_search)
    current_session.add(shared_search)
    current_session.flush()
    
    return shared_search