import pytest
from amanuensis.models import *


@pytest.fixture(scope="session")
def associated_users(session):
    associated_user_1 = AssociatedUser(
        user_id=1,
        user_source='fence',
        email='user1@example.com',
        active=True
    )

    associated_user_2 = AssociatedUser(
        user_id=2,
        user_source='fence',
        email='user2@example.com',
        active=True
    )

    update_associated_user_3 = AssociatedUser(
        user_id=3,
        user_source='fence',
        email='user3@example.com',
        active=True
    )

    update_associated_user_4 = AssociatedUser(
        user_id=4,
        user_source='fence',
        email='user4@example.com',
        active=True
    )

    session.add_all([associated_user_1, associated_user_2, update_associated_user_3, update_associated_user_4])
    session.commit()

    yield associated_user_1, associated_user_2, update_associated_user_3, update_associated_user_4



@pytest.fixture(scope="session", autouse=True)
def projects(session): 
    project_1 = Project(
        name='Sample Project 1',
        first_name='John',
        last_name='Doe',
        user_source='fence',
        institution='Sample Institution 1 ',
        description='A sample project description 1 ',
        approved_url='http://example.com/approved',
        active=True,
        user_id= 1
    )

    project_2 = Project(
        name='Sample Project 2',
        first_name='John',
        last_name='Doe',
        user_source='fence',
        institution='Sample Institution',
        description='A sample project description',
        approved_url='http://example.com/approved',
        active=True,
        user_id = 1
    )
    project_3 = Project(
        name='Sample Project 3',
        first_name='John',
        last_name='Doe',
        user_source='fence',
        institution='Sample Institution',
        description='A sample project description',
        approved_url='http://example.com/approved',
        active=True,
        user_id = 2
    )

    session.add_all([project_1, project_2, project_3])

    session.commit()

    # project_1_id = session.query(Project.id).filter(Project.name == 'Sample Project 1').first()[0]
    # project_2_id = session.query(Project.id).filter(Project.name == 'Sample Project 2').first()[0]
    # project_3_id = session.query(Project.id).filter(Project.name == 'Sample Project 3').first()[0]

    # yield project_1_id, project_2_id, project_3_id

    yield project_1, project_2, project_3


@pytest.fixture(scope="session", autouse=True)
def consortiums(session):

    consortium_1 = ConsortiumDataContributor(
        code="TEST1",
        name="TEST1"
    )

    consortium_2 = ConsortiumDataContributor(
        code="TEST2",
        name="TEST2"
    )

    consortium_3 = ConsortiumDataContributor(
        code="TEST3",
        name="TEST3"
    )

    session.add_all([consortium_2, consortium_1, consortium_3])
    session.commit()

    yield consortium_1, consortium_2, consortium_3


@pytest.fixture(scope="session", autouse=True)
def states(session):
    state_1 = State(name="STATE1", code="STATE1")
    state_2 = State(name="STATE2", code="STATE2")
    session.add_all(
        [
            state_1,
            state_2
        ]
    )

    session.commit()

    yield [state_1, state_2]


@pytest.fixture(scope="session", autouse=True)
def roles(session):

    role_1 = AssociatedUserRoles(
        code="TEST",
        role="TEST"
    )

    role_2 = AssociatedUserRoles(
        code="TEST2",
        role="TEST2"
    )

    session.add_all([role_1, role_2])
    session.commit()

    yield [role_1, role_2]


@pytest.fixture(scope="session", autouse=True)
def requests(session, projects, consortiums):
    #session.query(Request).delete()
    request_1 = Request(project=projects[0], consortium_data_contributor=consortiums[0])
    session.add_all(
        [
            request_1,
            Request(project=projects[1], consortium_data_contributor=consortiums[0]),
            Request(project=projects[1], consortium_data_contributor=consortiums[1]),
            Request(project=projects[2], consortium_data_contributor=consortiums[0]),
            Request(project=projects[2], consortium_data_contributor=consortiums[1]),
            Request(project=projects[2], consortium_data_contributor=consortiums[2]),
        ]
    )

    session.commit()



    yield request_1


    session.query(Request).delete()


@pytest.fixture(scope="session", autouse=True)
def searches(session):
    search_1 = Search(
        user_id=1,
        user_source="fence",
        name="Example Search",
        description="This is an example search.",
        filter_object={"param": "value"},
        filter_source=FilterSourceType.explorer,
        filter_source_internal_id=123,
        ids_list=["id1", "id2"],
        graphql_object={"field": "value"},
        es_index="index_name",
        dataset_version="1.0",
        is_superseded_by=None,
        active=True
    )

    search_2 = Search(
        user_id=2,
        user_source="fence",
        name="Example Search",
        description="This is an example search.",
        filter_object={"param": "value"},
        filter_source=FilterSourceType.manual,
        filter_source_internal_id=124,
        ids_list=["id1", "id2"],
        graphql_object={"field": "value"},
        es_index="index_name",
        dataset_version="1.0",
        is_superseded_by=None,
        active=True
    )

    search_3 = Search(
        user_id=3,
        user_source="fence",
        name="Example Search",
        description="This is an example search.",
        filter_object={"param": "value"},
        filter_source=FilterSourceType.manual,
        filter_source_internal_id=123,
        ids_list=["id1", "id2"],
        graphql_object={"field": "value"},
        es_index="index_name",
        dataset_version="1.0",
        is_superseded_by=None,
        active=True
    )

    session.add_all([search_1, search_2, search_3])

    session.commit()

    yield [search_1, search_2, search_3]



@pytest.fixture(scope="session", autouse=True)
def request_has_state(session, requests, states):
    req_state = RequestState(request=requests, state=states[0])
    session.add(req_state)
    session.commit()

    yield req_state

@pytest.fixture()
def delete_request_has_state(session):

    yield

    session.query(RequestState).delete()
    session.commit()


@pytest.fixture()
def delete_project_has_associated_user(session):
    
    yield

    session.query(ProjectAssociatedUser).delete()
    session.commit()