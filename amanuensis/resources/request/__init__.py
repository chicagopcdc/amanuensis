from amanuensis.schema import ProjectSchema

from amanuensis.resources.userdatamodel.project import get_projects
from amanuensis.resources.userdatamodel.search import get_filter_sets, create_filter_set
from amanuensis.resources.userdatamodel.state import get_states
from amanuensis.resources.consortium_data_contributor import get_consortiums_from_fitersets
from amanuensis.resources.userdatamodel.request_has_state import create_request_state, get_request_states
from amanuensis.resources.userdatamodel.request import create_request
from amanuensis.resources.userdatamodel.transition import get_transition_graph

from amanuensis.config import config
from amanuensis.errors import UserError, InternalError

from cdislogging import get_logger


logger = get_logger(__name__)


def change_request_state(session, project_id, state_id=None, state_code=None, consortium_list=None, filter_out_depricated=True):
        
    NEW_STATE = get_states(session, id=state_id, code=state_code, many=False, throw_not_found=True)    

    current_request_states = get_request_states(session, project_id=project_id, filter_out_depricated=filter_out_depricated, consortiums=consortium_list, latest=True)

    final_states = get_transition_graph(session, final_states=True)
    
    updated_requests = []

    for request_state in current_request_states: 
        if request_state.state.code in final_states:
            raise UserError(
                "Cannot change state of request {} from {} because it's a final state".format(
                    request_state.request.id, request_state.state.code
                )
            )
        updated_requests.append(create_request_state(session, request_state.request.id, NEW_STATE.id).request)

    return updated_requests

def calculate_overall_project_state(session, project_id=None, this_project_requests_states=None):
    """
    Takes status codes from all the requests within a project and returns the project status based on their precedence.
    Example: if all request status are "APPROVED", then the status code will be "APPROVED".
    However, if one of the request status is "PENDING", and "PENDING" has higher precedence
    then the status code will be "PENDING".
    """
    #run BFS on state flow chart
    if not this_project_requests_states:
        if project_id:
            this_project_requests_states = {request_state.state.code for request_state in get_request_states(session, project_id=project_id, filter_out_depricated=True, latest=True)}

    if not this_project_requests_states:
        return {"status": None}

    final_states = get_transition_graph(session, final_states=True)
    transition_graph = get_transition_graph(session, reverse=True)

    try: 
        
        for final_state in final_states:
            if final_state in this_project_requests_states:
                return {"status": final_state}   
             
        overall_state = None
        seen_codes = set()
        states_queue = ["DATA_DOWNLOADED"]
        while states_queue and this_project_requests_states:
            current_state = states_queue.pop(0)
            if current_state not in seen_codes:

                seen_codes.add(current_state)

                states_queue.extend(transition_graph[current_state] if current_state in transition_graph else [])
                
                if current_state in this_project_requests_states:

                    this_project_requests_states.remove(current_state)

                    if ((current_state == "APPROVED" and overall_state == "APPROVED_WITH_FEEDBACK")    
                        or (current_state == "REVISION" and overall_state == "SUBMITTED")):
                            continue
                    else:
                        overall_state = current_state
                        
        if this_project_requests_states:
            logger.error(f"{this_project_requests_states} dont exist in transition table")
            raise InternalError("")
        
        return {"status": overall_state}

    except Exception:
        raise InternalError("Unable to load or find the consortium status")


def project_requests_from_filter_sets(session, filter_set_ids=None, project_id=None, project=None, filter_sets=None):
    project_schema = ProjectSchema()
    
    # Retrieve the project
    project = get_projects(session, id=project_id, many=False, throw_not_found=True) if not project else project

    filter_sets = get_filter_sets(session, id=filter_set_ids, filter_by_source_type=False, throw_not_equal=True, throw_not_found=True) if not filter_sets else filter_sets

    project_filter_sets = []
    for filter_set in filter_sets:
        new_filter_set = create_filter_set(
            session,
            None,
            True,
            filter_set.filter_source_internal_id,
            project.name + "_" + filter_set.name,
            filter_set.description,
            filter_set.filter_object,
            filter_set.ids_list,
            filter_set.graphql_object,
            user_source=""
        )

        project_filter_sets.append(new_filter_set)

    
    #TODO block requests where filter-sets are part of project

    # list of requests to be included in the project
    new_consortiums = {consortium.code: consortium for consortium in get_consortiums_from_fitersets(project_filter_sets, session)}
    
    # list of requests that already exist in the project. requests in state Deprecated will not appear
    old_consortiums = {request_state.request.consortium_data_contributor.code for request_state in get_request_states(session, project_id=project.id, filter_out_depricated=True, latest=True)}

    # List of request to be moved to DEPRECATED
    remove_consortiums = old_consortiums - new_consortiums.keys()

    # list of requests to be created or moved from deprecated to IN_REVIEW
    add_consortiums = new_consortiums.keys() - old_consortiums

    # list of request to have their state changed
    update_consortiums = old_consortiums & new_consortiums.keys()
    if add_consortiums or remove_consortiums:
        if add_consortiums:
            IN_REVIEW = get_states(session, code="IN_REVIEW", many=False, throw_not_found=True)
            for consortium in add_consortiums:
                request = create_request(session, project_id=project.id, consortium_id=new_consortiums[consortium].id)
                create_request_state(session, request_id=request.id, state_id=IN_REVIEW.id)
        
        if remove_consortiums:
            change_request_state(session, project_id=project.id, state_code="DEPRECATED", consortium_list=list(remove_consortiums))

        change_request_state(session, project_id=project.id, state_code="IN_REVIEW", filter_out_depricated=False, consortium_list=list(update_consortiums))
    
    else:

        overall_project_state = calculate_overall_project_state(session, project_id=project.id)["status"]

        if overall_project_state == "DATA_DOWNLOADED" or overall_project_state == "DATA_AVAILABLE":
            change_request_state(session, project_id=project.id, state_code="APPROVED", filter_out_depricated=False, consortium_list=list(update_consortiums))
        
        else:
            change_request_state(session, project_id=project.id, state_code="IN_REVIEW", filter_out_depricated=False, consortium_list=list(update_consortiums))
    
    #check if any filter_sets were from tokens
    filter_set_ids = [fs.id for fs in filter_sets]
    are_filter_sets_shared = get_filter_sets(session, id=filter_set_ids, filter_by_source_type=False, filter_for_filterset_is_shared=True)
    if are_filter_sets_shared:
        for filter_set in are_filter_sets_shared:
            new_filter_set = create_filter_set(
                session,
                project.user_id,
                False,
                filter_set.filter_source_internal_id,
                filter_set.name + "_copied_from_project_" + str(project.id),
                filter_set.description,
                filter_set.filter_object,
                filter_set.ids_list,
                filter_set.graphql_object,
                user_source="fence"
            )


    project.searches = project_filter_sets

    session.flush()
    project_schema.dump(project)
    return project
    

    