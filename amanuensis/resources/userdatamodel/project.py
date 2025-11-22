from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError
from amanuensis.models import Project, ProjectAssociatedUser, AssociatedUser
from sqlalchemy import and_

logger = get_logger(__name__)

__all__ = [
    "get_projects",
    "create_project",
    "update_project"
]


def get_projects(
        current_session,
        active=True,
        filter_by_active=True,
        consortiums=None,
        user_id=None,
        associted_user_user_id=None,
        associated_user_email=None,
        id=None,
        name=None,
        many=True,
        throw_not_found=False
    ):
    
    projects = current_session.query(Project)

    #filter out deleted projects by default
    if filter_by_active:
        projects = projects.filter(Project.active == active)
    
    #get projects by id
    if id is not None:
        id = [id] if not isinstance(id, list) else id
        projects = projects.filter(Project.id.in_(id))

    if name is not None:
        name = [name] if not isinstance(name, list) else name
        projects = projects.filter(Project.name.in_(name))
    
    #get projects by consortium
    if consortiums:
        consortiums = [consortiums] if not isinstance(consortiums, list) else consortiums
        projects = projects.filter(Project.requests.consortium_data_contributor.code.in_(consortiums))

    if user_id:
        user_id = [user_id] if not isinstance(user_id, list) else user_id
        projects = projects.filter(Project.user_id.in_(user_id))

    
    if associted_user_user_id:
        associted_user_user_id = [associted_user_user_id] if not isinstance(associted_user_user_id, list) else associted_user_user_id
        projects = projects.filter(Project.associated_users_roles.any(and_(ProjectAssociatedUser.associated_user.has(AssociatedUser.user_id.in_(associted_user_user_id)), ProjectAssociatedUser.active == True)))

    if associated_user_email:
        associated_user_email = [associated_user_email] if not isinstance(associated_user_email, list) else associated_user_email
        projects = projects.filter(Project.associated_users_roles.any(and_(ProjectAssociatedUser.associated_user.has(AssociatedUser.email.in_(associated_user_email)), ProjectAssociatedUser.active == True)))


    projects = projects.all()


    if throw_not_found and not projects:
        raise NotFound(f"No projects found")

    if not many:
        if len(projects) > 1:
            raise UserError(f"More than one project found check inputs")
        else:
            projects = projects[0] if projects else None
    
    return projects


def create_project(current_session, user_id, description, name, institution):
    """
    Creates a project with an associated auth_id and storage access
    """

    project = get_projects(current_session, name=name, many=False)

    if project:
        """
        Return json message of name already exists
        """
        raise UserError(f"Projects with name {name} already exists")


    new_project = Project(
        user_id=user_id,
        user_source="fence",
        description=description,
        institution=institution,
        name=name,
    )

    current_session.add(new_project)

    current_session.flush()

    return new_project


def update_project(current_session, 
                   id,
                   first_name=None, 
                   last_name=None, 
                   user_id=None, 
                   user_source=None, 
                   description=None, 
                   institution=None, 
                   name=None,
                   approved_url=None,
                   delete=False
):
    
    project = get_projects(current_session, id=id, many=False, throw_not_found=True)

    project.first_name = first_name if first_name is not None else project.first_name
    project.last_name = last_name if last_name is not None else project.last_name
    project.user_id = user_id if user_id is not None else project.user_id
    project.user_source = user_source if user_source is not None else project.user_source
    project.description = description if description is not None else project.description
    project.institution = institution if institution is not None else project.institution
    project.name = name if name is not None else project.name
    project.approved_url = approved_url if approved_url is not None else project.approved_url
    project.active = True if not delete else False

    current_session.flush()

    return project