from amanuensis.errors import NotFound, UserError
from amanuensis.models import Search, FilterSourceType
from cdislogging import get_logger
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
        many=True,
        filter_by_active=True,
        filter_by_source_type=True,
        throw_not_found=False,
        throw_not_equal=False
):
    filter_sets = current_session.query(Search)

    logger.info(f"get_filter_sets: {locals()}")

    if filter_by_active:
        filter_sets = filter_sets.filter(Search.active == active)

    if filter_by_source_type:
        filter_sets = filter_sets.filter(Search.filter_source == FilterSourceType.explorer)
    
    
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


    if user_id:
        user_id = [user_id] if not isinstance(user_id, list) else user_id
        filter_sets = filter_sets.filter(Search.user_id.in_(user_id))


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
        graphql_object
    ):

    new_filter_set = Search(
        user_id=logged_user_id,
        user_source="fence",
        name=name,
        description=description,
        filter_object=filter_object,
        filter_source=FilterSourceType.manual if is_amanuensis_admin else FilterSourceType.explorer,
        filter_source_internal_id=explorer_id,
        ids_list=ids_list,
        graphql_object=graphql_object
    )
    # TODO add es_index, add dataset_version
    current_session.add(new_filter_set)
    current_session.commit()

    return new_filter_set


def update_filter_set(
        current_session, 
        logged_user_id, 
        filter_set_id, 
        explorer_id, 
        name=None, 
        description=None, 
        filter_object=None, 
        graphql_object=None,
        delete=False
    ):
    

    filter_set = get_filter_sets(current_session, id=filter_set_id, explorer_id=explorer_id, user_id=logged_user_id, many=False, throw_not_found=True)

    filter_set.name = name if name is not None else filter_set.name
    filter_set.description = description if description is not None else filter_set.description
    filter_set.filter_object = filter_object if filter_object is not None else filter_set.filter_object
    filter_set.graphql_object = graphql_object if graphql_object is not None else filter_set.graphql_object
    filter_set.active = True if not delete else False

    current_session.commit()

    return filter_set

