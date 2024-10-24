from amanuensis.models import ProjectSearch
from amanuensis.errors import NotFound, UserError
from cdislogging import get_logger
logger = get_logger(__name__)

__all__ = [
    "get_project_searches",
    "create_project_search",
]


def get_project_searches(current_session, project_id=None, filter_set_id=None, throw_not_found=False, many=True):

    project_searches = current_session.query(ProjectSearch)

    if project_id:
        project_id = [project_id] if not isinstance(project_id, list) else project_id
        project_searches = project_searches.filter(ProjectSearch.project_id.in_(project_id))

    if filter_set_id:
        filter_set_id = [filter_set_id] if not isinstance(filter_set_id, list) else filter_set_id
        project_searches = project_searches.filter(ProjectSearch.filter_set_id.in_(filter_set_id))

    project_searches = project_searches.all()

    if throw_not_found and not project_searches:
        raise NotFound(f"No project searches found")

    if not many:
        if len(project_searches) > 1:
            raise UserError(f"More than one project search found check inputs")
        else:
            project_searches = project_searches[0] if project_searches else None

    return project_searches


def create_project_search(current_session, project_id, filter_set_id):
    
    if get_project_searches(current_session, project_id=project_id, filter_set_id=filter_set_id, many=False):
        logger.info(f"ProjectSearch already exists: {project_id} {filter_set_id}")
    else:
        project_search = ProjectSearch(project_id=project_id, filter_set_id=filter_set_id)
        current_session.add(project_search)
        current_session.commit()
        
    return project_search
