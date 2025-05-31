import pytest
from amanuensis.errors import NotFound, UserError
from amanuensis.models import Search, SearchIsShared, ProjectSearch
from amanuensis.scripting.clear_old_filter_sets import main




def test_clear_unused_filter_sets(session, client, register_user, login, mock_requests_post, pytestconfig, filter_set_post, filter_set_snapshot_post, project_post, admin_copy_search_to_user_post, admin_copy_search_to_project, admin_filter_set_post):
    # Validate initial state
    # User creates filter-set via UI and has user_id
    # User creates project, and a new search without a user_id is created and added to project_has_search
    # User creates snapshot, and a new search without a user_id is created and added to search_is_shared
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    user_id_2, user_email_2 = register_user(email=f"user_2@{__name__}.com", name=__name__)
    admin_id, admin_email = register_user(email=f"admin@{__name__}", name=__name__, role="admin")

    login(user_id, user_email)

    #1 This will be deleted becuase it has no ids list and no graphql_object and no filter_object
    search_1_id = filter_set_post(
        user_id, 
        name=f"search_1_{__name__}"
    ).json["id"]

    #2 this will not be deleted bc filter_object is present and graphql_object is present
    search_2_id = filter_set_post(
        user_id, 
        name=f"search_2_{__name__}", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    
    login(user_id_2, user_email_2)
    #3 this will not be deleted bc filter_object is presetn
    search_3_id = filter_set_post(
        user_id_2, 
        name=f"search_3_{__name__}", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
    ).json["id"]

    login(user_id, user_email)
    #4 this will not be deleted bc its part of search_is_shared
    filter_set_snapshot_post(
        user_id,
        filter_set_id=search_1_id
    )

    login(admin_id, admin_email)
    #5 this will not be deleted bc it has graphql_object and filter_object
    admin_copy_search_to_user_post(
        admin_id,
        user_id=user_id_2,
        filter_set_id=search_2_id
    )
    
    #6 will be deleted by #7 bc is is no longer part of the project has search and has no user_id
    login(user_id, user_email)
    project_id = project_post(
        user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        associated_users_emails=[user_email],
        name=f"{__name__}_project",
        description="This is an endpoint test project",
        institution="test university",
        filter_set_ids=[search_2_id],
    ).json["id"]

    login(admin_id, admin_email)
    #7 this will not be deleted bc it is part of the project has search
    admin_copy_search_to_project(
        admin_id,
        filter_set_id=search_3_id,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
    )

    #8 this will be deleted 
    blank_1 = Search(
        user_id=user_id,
        name=f"search_1_blank_{__name__}",
        filter_object=None,
        graphql_object={},
    )

    #9 this will be deleted
    blank_2 = Search(
        user_id=user_id,
        name=f"search_2_blank_{__name__}",
        filter_object={},
        graphql_object=None,
    )

    #10 this will be deleted
    blank_3 = Search(
        user_id=user_id,
        name=f"search_3_blank_{__name__}",
        filter_object={},
        graphql_object={},
    )
    #11 this will be deleted
    blank_4 = Search(
        user_id=user_id,
        name=f"search_4_blank_{__name__}",
        filter_object=None,
        graphql_object=None,
    )
    session.add_all([blank_1, blank_2, blank_3, blank_4])
    session.commit()

    login(admin_id, admin_email)
    #12 this will not be deleted bc it has graphql_object
    admin_filter_set_post(
        admin_id,
        user_id=user_id,
        name=f"search_1_admin_{__name__}",
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    )
    #13 this will not be deleted bc it has ids list
    admin_filter_set_post(
        admin_id,
        user_id=user_id,
        name=f"search_2_ids_list_admin_{__name__}",
        ids_list=["this_is_an_id"],
    )
    #14 this will be deleted bc it has no ids list and no graphql_object and no filter_object
    admin_filter_set_post(
        admin_id,
        user_id=user_id,
        name=f"no_data_admin_{__name__}",
    )
    assert session.query(Search).count() == 14
    assert session.query(Search).filter(Search.user_id.is_(None)).count() == 3
    assert session.query(SearchIsShared).count() == 1
    assert session.query(ProjectSearch).count() == 1

    # Run main function
    main(["--file_name", pytestconfig.getoption("--configuration-file")])

    assert session.query(Search).count() == 7
    assert session.query(Search).filter(Search.user_id.is_(None)).count() == 2
    assert session.query(SearchIsShared).count() == 1
    assert session.query(ProjectSearch).count() == 1

    assert not session.query(Search).filter(Search.id == search_1_id).first()
    assert not session.query(Search).filter(Search.name == f"{__name__}_project_search_2_{__name__}").first()
    assert not session.query(Search).filter(Search.name == f"search_1_blank_{__name__}").first()
    assert not session.query(Search).filter(Search.name == f"search_2_blank_{__name__}").first()
    assert not session.query(Search).filter(Search.name == f"search_3_blank_{__name__}").first()
    assert not session.query(Search).filter(Search.name == f"search_4_blank_{__name__}").first()
    assert not session.query(Search).filter(Search.name == f"no_data_admin_{__name__}",).first()

