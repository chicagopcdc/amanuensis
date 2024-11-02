from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Request,
    ConsortiumDataContributor,
    Project
)

__all__ = [
    "get_requests",
    "create_request",
]

def get_requests(
        current_session, 
        id=None, 
        user_id=None, 
        consortiums=None, 
        project_id=None,
        many=True,
        throw_not_found=False
    ):

    requests = current_session.query(Request)

    if user_id:
        user_id = [user_id] if not isinstance(user_id, list) else user_id
        requests = requests.filter(Request.project.has(Project.user_id.in_(user_id)))
    
    if id is not None:
        id = [id] if not isinstance(id, list) else id
        requests = requests.filter(Request.id.in_(id))
    

    if consortiums:
        consortiums = [consortiums] if not isinstance(consortiums, list) else consortiums
        requests = requests.filter(Request.consortium_data_contributor.has(ConsortiumDataContributor.code.in_(consortiums)))
        
    if project_id:
        project_id = [project_id] if not isinstance(project_id, list) else project_id
        requests = requests.filter(Request.project_id.in_(project_id))


    requests = requests.all()

    if throw_not_found and not requests:
        raise NotFound(f"No requests found")

    if not many:
        if len(requests) > 1:
            raise UserError(f"More than one request found check inputs")
        else:
            requests = requests[0] if requests else None
    
    return requests


def create_request(current_session, project_id, consortium_id):
    request = Request(
        project_id=project_id,
        consortium_data_contributor_id=consortium_id
    )

    current_session.add(request)


    current_session.flush()

    return request