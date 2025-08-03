from cdislogging import get_logger
from amanuensis.models import ProjectDataPoints, Project
from amanuensis.errors import NotFound, UserError

logger = get_logger(__name__)

__all__ = [
    "get_project_datapoints",
    "create_project_datapoints",
    "update_project_datapoints"
]

def get_project_datapoints(
        current_session, #session of the database
        term=None, #term which is being serched against
        id=None, #id of the datapoints key
        project_id=None, #id associated with a certain project
        type=None, #user wants a specific datapoints type: 'w' or 'b'
        throw_not_found=True, #throws error if query returns no rows
        many=False #true if you want the option of multiple rows
    ):
    """
    accesses project_datapoints from the project_datapoints table based on the 
    inputed column information specifiers
    """
    
    projectDataPoints = current_session.query(ProjectDataPoints)

    #only gets the active datapoints
    projectDataPoints = projectDataPoints.filter(ProjectDataPoints.active == True)

    #only gets the projectDataPoints with the given project_datapoints.id
    if id is not None:
        projectDataPoints = projectDataPoints.filter(ProjectDataPoints.id == id)

    #only gets the projectDataPoints with the given project_datapoints.term
    if term is not None:
        projectDataPoints = projectDataPoints.filter(ProjectDataPoints.term == term)

    #only gets the projectDataPoints with the given project_datapoints.project_id
    if project_id is not None:
        projectDataPoints = projectDataPoints.filter(ProjectDataPoints.project_id == project_id)

    #only gets the projectDataPoints with the given project_datapoints.type
    if type is not None:
        projectDataPoints = projectDataPoints.filter(ProjectDataPoints.type == type)

    projectDataPoints = projectDataPoints.all()

    if not projectDataPoints and throw_not_found:
        raise NotFound("No ProjectDataPoints found")
    
    #deals with returning one versus multiple rows
    if not many:
        projectDataPoints = projectDataPoints[0] if projectDataPoints else None

    return projectDataPoints

def create_project_datapoints(
    current_session,
    term,
    value_list,
    type,
    project_id
    ):
    """
    adds a new row to the project_datapoints table

    returns projectDataPoints model if project_datapoints did not already exist
    returns None if projectDataPoints already exists in the database table 
    """

    #checking if project with inputed id exists within the db
    project_exists = current_session.query(Project.id).filter_by(id=project_id).first()
    if not project_exists:
        raise UserError("Invalid project_id: project does not exist")
    
    #checks if the inputted type is 'w' or 'b'
    if type not in ['w','b']:
        raise UserError("datapoints type may only be: 'b' for blacklist, or 'w' for whitelist")

    pre_existing_datapoints = get_project_datapoints(current_session, term=term, type=type, project_id=project_id, throw_not_found=False)

    #checks if the term already exists within the database
    if pre_existing_datapoints:
        raise UserError(f"Project_DataPoints with term {term} and {'whitelist' if type =='w' else 'blacklist'} datapoints type")

    datapoint = current_session.query(ProjectDataPoints)
    datapoint = datapoint.filter(ProjectDataPoints.active == False)
    datapoint = datapoint.filter(ProjectDataPoints.type == type)
    datapoint = datapoint.filter(ProjectDataPoints.project_id == project_id)
    datapoint = datapoint.filter(ProjectDataPoints.term == term).all()

    if  len(datapoint) > 1:
        raise ValueError("Expected at most one result, but got multiple rows.")
    elif datapoint:
        datapoint = datapoint[0]
        # reactivate the deactivated datapoint and give it the value list of new creation
        datapoint.active = True
        datapoint.value_list = value_list
        datapoint = datapoint

    else:
        datapoint = ProjectDataPoints(
            term = term,
            value_list = value_list,
            type = type,
            project_id = project_id,
            active = True,
        )
        current_session.add(datapoint)

    current_session.flush()
    return datapoint

def update_project_datapoints(current_session,
                   id,
                   term=None,
                   value_list=None,
                   project_id=None,
                   type=None, #change the datapoints type of the row 'w' or 'b'
                   delete=False, #signal for the deletion of a row in the database
    ):
    """
    updates a row in the table with information given an id for the project_datapoints
    """

    prev_datapoints = get_project_datapoints(current_session,id=id,many=False,throw_not_found= True)
    
    if delete:
        # changes the activation value to false
        prev_datapoints.active = False
    else:
        prev_datapoints.term = term if term is not None else prev_datapoints.term
        prev_datapoints.value_list = value_list if value_list is not None else prev_datapoints.value_list
        prev_datapoints.project_id = project_id if project_id is not None else prev_datapoints.project_id
        if(type is not None):
            if type not in ['w','b']:
                raise UserError("datapoints type may only be: 'b' for blacklist, or 'w' for whitelist")
            prev_datapoints.type = type

    current_session.flush()
    return prev_datapoints