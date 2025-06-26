from amanuensis.errors import NotFound, UserError, InternalError
from amanuensis.models import Search, FilterSourceType, ProjectSearch, SearchIsShared
from cdislogging import get_logger
from sqlalchemy import exists
logger = get_logger(__name__)
__all__ = [
    "get_filter_sets",
    "create_filter_set",
    "update_filter_set"
]

def get_filter_sets(
        current_session,
        explorer_id=None,
        active=True, 
        id=None,
        user_id=None,
        graphql_object=None,
        filter_object=None,
        ids_list=None,
        source_type=FilterSourceType.explorer,
        filter_by_active=True,
        filter_by_source_type=True,
        filter_by_ids_list=False,
        filter_for_no_user_id=False,
        filter_for_not_shared_filtersets=False,
        filter_for_not_project_filtersets=False,
        throw_not_found=False,
        throw_not_equal=False,
        many=True,
):
    filter_sets = current_session.query(Search)

    logger.info(f"get_filter_sets: {locals()}")

    if filter_by_active:
        filter_sets = filter_sets.filter(Search.active == active)

    if filter_by_source_type:
        filter_sets = filter_sets.filter(Search.filter_source == source_type)
    
    
    if explorer_id is not None:
        explorer_id = [explorer_id] if not isinstance(explorer_id, list) else explorer_id
        filter_sets = filter_sets.filter(Search.filter_source_internal_id.in_(explorer_id))
    
    if id is None and throw_not_equal:
        raise UserError("You must pass a filter_set_id")

    if id is not None:
        id = [id] if not isinstance(id, list) else id
        filter_sets = filter_sets.filter(Search.id.in_(id))
        if throw_not_equal:
            must_match = len(id)
    elif throw_not_equal:
        raise UserError("You must pass a filter_set_id to enforce equality check")

    if filter_object is not None:
        filter_object = [filter_object] if not isinstance(filter_object, list) else filter_object
        filter_sets = filter_sets.filter(Search.filter_object.in_(filter_object))
    
    if graphql_object is not None:
        graphql_object = [graphql_object] if not isinstance(graphql_object, list) else graphql_object
        filter_sets = filter_sets.filter(Search.graphql_object.in_(graphql_object))
    
    if filter_by_ids_list:
        filter_sets = filter_sets.filter(Search.ids_list.is_(ids_list))

    if user_id:
        user_id = [user_id] if not isinstance(user_id, list) else user_id
        filter_sets = filter_sets.filter(Search.user_id.in_(user_id))

    if filter_for_no_user_id:
        filter_sets = filter_sets.filter(Search.user_id.is_(None))
    if filter_for_not_shared_filtersets:
        filter_sets = filter_sets.filter(~exists().where(SearchIsShared.search_id == Search.id))
    if filter_for_not_project_filtersets:
        filter_sets = filter_sets.filter(~exists().where(ProjectSearch.search_id == Search.id))
        
        

    filter_sets = filter_sets.all()

    if throw_not_found and not filter_sets:
        raise NotFound(f"No filter_sets found")
    
    if throw_not_equal and len(filter_sets) != must_match:
        raise UserError(f"{must_match} filter_sets were submitted but {len(filter_sets)} found")

    if not many:
        if len(filter_sets) > 1:
            raise UserError(f"More than one filter_set found check inputs")
        else:
            filter_sets = filter_sets[0] if filter_sets else None 
        
    
    return filter_sets


def create_filter_set(
        current_session, 
        logged_user_id, 
        is_amanuensis_admin, 
        explorer_id, 
        name, 
        description, 
        filter_object, 
        ids_list, 
        graphql_object,
        user_source="fence"
    ):

    new_filter_set = Search(
        user_id=logged_user_id,
        user_source=user_source,
        name=name,
        description=description,
        filter_object={} if filter_object is None else filter_object,
        filter_source=FilterSourceType.manual if is_amanuensis_admin else FilterSourceType.explorer,
        filter_source_internal_id=explorer_id,
        ids_list=ids_list,
        graphql_object={} if graphql_object is None else graphql_object
    )
    # TODO add es_index, add dataset_version
    current_session.add(new_filter_set)
    current_session.flush()

    return new_filter_set


def update_filter_set(
        current_session, 
        filter_set=None,
        logged_user_id=None, 
        filter_set_id=None, 
        explorer_id=None, 
        name=None, 
        description=None, 
        filter_object=None, 
        graphql_object=None,
        is_valid=None,
        delete=False
    ):
    
    

    if filter_set is not None:
        if not isinstance(filter_set, Search):
            raise InternalError("filter_set must be a Search object")
        
    else:
        filter_set = get_filter_sets(current_session, id=filter_set_id, explorer_id=explorer_id, user_id=logged_user_id, many=False, throw_not_found=True)

    
    if is_valid is not None:
        filter_set.is_valid = is_valid
    
    elif filter_object is not None or graphql_object is not None:
        filter_set.is_valid = True

    filter_set.name = name if name is not None else filter_set.name
    filter_set.description = description if description is not None else filter_set.description
    filter_set.filter_object = filter_object if filter_object is not None else filter_set.filter_object
    filter_set.graphql_object = graphql_object if graphql_object is not None else filter_set.graphql_object
    filter_set.active = True if not delete else False

    current_session.flush()

    return filter_set

def hard_delete_filter_set(
        session,
        graphql_object=None,
        filter_object=None,
        ids_list=None,
        filter_by_active=False,
        filter_by_source_type=False,
        filter_by_ids_list=False,
        filter_for_no_user_id=False,
        filter_for_not_shared_filtersets=False,
        filter_for_not_project_filtersets=False,

    ):
    
    filter_sets = get_filter_sets(
        session,
        filter_object=filter_object,
        graphql_object=graphql_object,
        ids_list=ids_list,
        filter_by_ids_list=filter_by_ids_list,
        filter_by_active=filter_by_active, 
        filter_by_source_type=filter_by_source_type,
        filter_for_no_user_id=filter_for_no_user_id,
        filter_for_not_shared_filtersets=filter_for_not_shared_filtersets,
        filter_for_not_project_filtersets=filter_for_not_project_filtersets,
        many=True,
        throw_not_found=False,
        throw_not_equal=False,
    )

    for filter_set in filter_sets:
        logger.info(f"Deleting filter_set NAME: {filter_set.name} ID: {filter_set.id}")
        session.delete(filter_set)
    
    
    session.flush()
  
                           