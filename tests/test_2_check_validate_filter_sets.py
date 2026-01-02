import pytest
from amanuensis.resources.filter_sets import _load_data_files, _get_selectable_filters_from_data_portal, _check_es_to_dd_map, _check_portal_config, check_filter_sets, _extract_selected_values_from_filter_set
from amanuensis.errors import NotFound, InternalError
from amanuensis.models import Search, SearchIsShared, Project, FilterSourceType
from amanuensis.scripting.validate_filter_sets import main
import json
import os


@pytest.fixture(scope="module")
def es_to_dd_map():
    mapping = _load_data_files("es_to_dd_map.json")
    yield mapping

@pytest.fixture(scope="module")
def portal_config():
    portal_config = _load_data_files("gitops.json")
    yield portal_config

pytest.mark.order(1)
def test__load_data_files():
    assert _load_data_files("es_to_dd_map.json")
    assert _load_data_files("gitops.json")
    with pytest.raises(InternalError):
        _load_data_files("not_real.json")

pytest.mark.order(3)
def test__get_selectable_filters_from_data_portal(portal_config):
    assert _get_selectable_filters_from_data_portal(portal_config)

pytest.mark.order(4)
def test__extract_selected_values_from_filter_set():
    #check basic
    graphql_object_1_valid = {"AND":[{"IN":{"consortium":["INRG"]}}]}
    result_1 = _extract_selected_values_from_filter_set(graphql_object_1_valid)
    assert result_1 == {"consortium": ["INRG"]}

    #check nested
    graphql_object_2_valid = {
        "OR": [
            {
                "IN": {
                    "consortium": [
                    "INRG"
                    ]
                }
            },
            {
                "nested": {
                    "path": "histologies",
                    "OR": [
                    {
                        "IN": {
                        "histology": [
                            "Ganglioneuroblastoma, Intermixed (Schwannian Stroma-Rich)"
                        ]
                        }
                    },
                    {
                        "IN": {
                        "histology_grade": [
                            "Differentiating",
                            "Unknown"
                        ]
                        }
                    }
                    ]
                }
            },
        ]
    }
    result_2 = _extract_selected_values_from_filter_set(graphql_object_2_valid)
    assert result_2 == {"consortium": ["INRG"], "histologies.histology": ["Ganglioneuroblastoma, Intermixed (Schwannian Stroma-Rich)"], "histologies.histology_grade": ["Differentiating", "Unknown"]}

    #check compose
    graphql_object_3_valid = {"AND":[{"AND":[{"IN":{"consortium":["INRG"]}}]},{"AND":[{"IN":{"consortium":["INRG"]}}]}]}
    result_3 = _extract_selected_values_from_filter_set(graphql_object_3_valid)
    assert result_3 == {"consortium": ["INRG", "INRG"]}
    #check GTE, LTE, !=
    graphql_object_4_valid = {
        "OR": [
            {
                "nested": {
                    "path": "tumor_assessments",
                    "OR": [
                        {
                            "AND": [
                            {
                                "GTE": {
                                "age_at_tumor_assessment": 2261
                                }
                            },
                            {
                                "LTE": {
                                "age_at_tumor_assessment": 7503
                                }
                            }
                            ]
                        },
                        {
                            "AND": [
                            {
                                "!=": {
                                "tumor_classification": "Metastatic"
                                }
                            }
                            ]
                        }
                    ]
                }
            }
        ]
    }
   
    result_4 = _extract_selected_values_from_filter_set(graphql_object_4_valid)

    assert result_4 == {"tumor_assessments.age_at_tumor_assessment": [2261, 7503], "tumor_assessments.tumor_classification": ["Metastatic"]}

    #check invalid bad key
    graphql_object_1_invalid = {"AND":[{"NOT_REAL":{"consortium":["INRG"]}}]}
    result_1 = _extract_selected_values_from_filter_set(graphql_object_1_invalid)
    assert result_1 == False

    #check invalid mising path 
    graphql_object_2_invalid = {
        "OR": [
            {
                "nested": {
                    "OR": [
                        {
                            "AND": [
                            {
                                "GTE": {
                                "age_at_tumor_assessment": 2261
                                }
                            },
                            {
                                "LTE": {
                                "age_at_tumor_assessment": 7503
                                }
                            }
                            ]
                        },
                        {
                            "AND": [
                            {
                                "!=": {
                                "tumor_classification": "Metastatic"
                                }
                            }
                            ]
                        }
                    ]
                }
            }
        ]
    }
    result_2 = _extract_selected_values_from_filter_set(graphql_object_2_invalid)
    assert result_2 == False

    #no value for filter-set
    graphql_object_3_invalid = {"AND":[{"IN":{"consortium":[]}}]}
    result_3 = _extract_selected_values_from_filter_set(graphql_object_3_invalid)
    assert result_3 == False

pytest.mark.order(5)
def test_check_portal_config(portal_config):
    selectable_filters = _get_selectable_filters_from_data_portal(portal_config)

    #check valid
    assert _check_portal_config({"sex", "consortium"}, "test_valid_filter_set", selectable_filters[1])

    #check invalid for both sections
    assert not _check_portal_config({"sex", "consortium", "invalid"}, "test_invalid_filter_set", selectable_filters[1])

    assert not _check_portal_config({"sex", "consortium", "invalid"}, "test_invalid_filter_set", selectable_filters[2])

    #check invalid for only one section

    assert  _check_portal_config({"sex", "consortium", "subject_responses.tx_prior_response"}, "test_valid_filter_set_for_1", selectable_filters[1])

    assert not _check_portal_config({"sex", "consortium", "subject_responses.tx_prior_response"}, "test_invalid_filter_set_for_2", selectable_filters[2])

pytest.mark.order(6)
def test_check_es_to_dd_map(es_to_dd_map):

    #test valid enums
    assert _check_es_to_dd_map({"sex": ["Male"], "consortium": ["INRG", "INSTRuCT", "INRG"]}, "test_valid_filter_set", es_to_dd_map)

    #test valid type number
    assert _check_es_to_dd_map({"tumor_assessments.longest_diam_dim1": [76, 91]}, "test_valid_filter_set", es_to_dd_map)

    #test valid type string
    assert _check_es_to_dd_map({"labs.lab_result": ["0001"]}, "test_valid_filter_set", es_to_dd_map)

    #test valid manual entry, no pointer but has enum
    assert _check_es_to_dd_map({"survival_characteristics.lkss_obfuscated": ["Known"]}, "test_valid_filter_set", es_to_dd_map)

    #test filter not in elastic search
    assert not _check_es_to_dd_map({"sex": ["Male"], "not_real": ["some_study"]}, "test_invalid_filter_set", es_to_dd_map)

    #test filter in elastic search and not in data dictionary
    assert not _check_es_to_dd_map({"sex": ["Male"], "_molecular_analysis_count": ["some_molecular_analysis_count"]}, "test_invalid_filter_set", es_to_dd_map)

    #test es_to_dd_map has bad value, points to something but has no type or enum
    save_enum = es_to_dd_map["consortium"]["enum"]
    del es_to_dd_map["consortium"]["enum"]
    with pytest.raises(InternalError):
        _check_es_to_dd_map({"consortium": ["INRG"]}, "test_invalid_filter_set", es_to_dd_map)
    es_to_dd_map["consortium"]["enum"] = save_enum

    #test filter has enum no longer supported 
    assert not _check_es_to_dd_map({"consortium": ["INRG", "fake_enum"]}, "test_invalid_filter_set", es_to_dd_map)

    #test type string contains none string value 
    assert not _check_es_to_dd_map({"labs.lab_result": ["1234", 12]}, "test_invalid_filter_set", es_to_dd_map)

    #test type number contains none number value
    assert not _check_es_to_dd_map({"tumor_assessments.longest_diam_dim1": [76, "91"]}, "test_invalid_filter_set", es_to_dd_map)

    #test type number container a float
    assert _check_es_to_dd_map({"tumor_assessments.longest_diam_dim1": [76, 91.0]}, "test_invalid_filter_set", es_to_dd_map)

pytest.mark.order(7)
def test_check_filter_sets(session,  
                           pytestconfig,
                           filter_set_post, 
                           admin_filter_set_post, 
                           project_post, 
                           admin_copy_search_to_user_post,
                           filter_set_snapshot_post,
                           register_user,
                           login,
                           ):
    user_id, user_email = register_user(email=f"user_1@{test_check_filter_sets}.com", name=test_check_filter_sets)
    user_2_id, user_2_email = register_user(email=f"user_2@{test_check_filter_sets}.com", name=test_check_filter_sets)
    admin_id, admin_email = register_user(email=f"admin@{test_check_filter_sets}.com", name=test_check_filter_sets, role="admin")

    fake_graphql_object = {"AND":[{"IN":{"consortium":["NOT_REAL"]}}]}
    real_graphql_object = {"AND":[{"IN":{"consortium":["INRG"]}}]}
    invalid_for_portal_valid_for_data_dictionary = {"AND":[{"IN":{"subject_responses.tx_prior_response":["Chemotherapy"]}}]}
    malformed_graphql_object = {"AND":[{"NOT_REAL":{"consortium":["INRG"]}}]} 

    login(user_id, user_email)

    filter_set_post_real = filter_set_post(
        user_id,
        name="valid_filter_set_from_filter_set_post",
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
        graphql_object=real_graphql_object,
        description="valid_filter_set_from_filter_set_post",
        )

    filter_set_post_invalid = filter_set_post(
        user_id,
        name="invalid_filter_set_from_filter_set_post",
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
        graphql_object=fake_graphql_object,
        description="invalid_filter_set_from_filter_set_post",
        )
    
    filter_set_post_invalid_for_portal_valid_for_data_dictionary = filter_set_post(
        user_id,
        name="invalid_for_portal_valid_for_data_dictionary",
        explorer_id=2,
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"subject_responses.tx_prior_response":{"__type":"OPTION","selectedValues":["Chemotherapy"],"isExclusion":False}}},
        graphql_object=invalid_for_portal_valid_for_data_dictionary,
        description="invalid_for_portal_valid_for_data_dictionary",
        )

    filter_set_post_malformed = filter_set_post(
        user_id,
        name="malformed_filter_set_from_filter_set_post",
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
        graphql_object=malformed_graphql_object,
        description="malformed_filter_set_from_filter_set_post",
        )
    
    filter_set_no_graphql_object = filter_set_post(
        user_id,
        name="no_graphql_object_filter_set_from_filter_set_post",
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
        description="no_graphql_object_filter_set_from_filter_set_post",
        graphql_object={},
        )

    session.query(Search).filter(Search.id==filter_set_no_graphql_object.json["id"]).update({"graphql_object": None})
    session.commit()

    login(admin_id, admin_email)

    admin_filter_set_post_real = admin_filter_set_post(
        admin_id,
        user_id=user_id,
        name="valid_filter_set_from_admin_filter_set_post",
        graphql_object=real_graphql_object,
        description="valid_filter_set_from_admin_filter_set_post",
        )
    admin_filter_set_post_invalid = admin_filter_set_post(
        admin_id,
        user_id=user_id,
        name="invalid_filter_set_from_admin_filter_set_post",
        graphql_object=fake_graphql_object,
        description="invalid_filter_set_from_admin_filter_set_post",
        )
    
    login(user_id, user_email)

    project_post_real = project_post(
        user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INRG"],
        name="valid_filter_set_from_project_post",
        filter_set_ids=[filter_set_post_real.json["id"]],
        description="valid_filter_set_from_project_post",
        institution="valid_filter_set_from_project_post",
        explorer_id=1,
        )
    
    project_post_invalid = project_post(
        user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INRG"],
        name="invalid_filter_set_from_project_post",
        filter_set_ids=[filter_set_post_invalid.json["id"]],
        description="invalid_filter_set_from_project_post",
        institution="invalid_filter_set_from_project_post",
        explorer_id=1,
        )
    
    login(admin_id, admin_email)

    admin_copy_search_to_user_post_real = admin_copy_search_to_user_post(
        admin_id,
        user_id=user_2_id,
        filter_set_id=filter_set_post_real.json["id"],
        )
    
    admin_copy_search_to_user_post_invalid = admin_copy_search_to_user_post(
        admin_id,
        user_id=user_2_id,
        filter_set_id=filter_set_post_invalid.json["id"],
        )
    
    login(user_id, user_email)
    
    filter_set_snapshot_post_real = filter_set_snapshot_post(
        user_id,
        filter_set_id=filter_set_post_real.json["id"],
        )
    
    filter_set_snapshot_post_invalid = filter_set_snapshot_post(
        user_id,
        filter_set_id=filter_set_post_invalid.json["id"],
        )

    #generate bad filter set missing filter_source

    filter_set_no_filter_source = Search(
            name="filter_set_no_filter_source",
            description="filter_set_no_filter_source",
            filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
            graphql_object=real_graphql_object,
            filter_source_internal_id=1,
    )

    filter_set_no_filter_source_internal_id = Search(
            name="filter_set_no_filter_source_internal_id",
            description="filter_set_no_filter_source_internal_id",
            filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
            graphql_object=real_graphql_object,
            filter_source=FilterSourceType.explorer
    )

    session.add_all([filter_set_no_filter_source, filter_set_no_filter_source_internal_id])
    session.commit()
    main(["--file_name", pytestconfig.getoption("--configuration-file")])

    assert session.query(Search).filter(Search.id==filter_set_post_real.json["id"]).first().is_valid
    assert session.query(Search).filter(Search.id==filter_set_post_invalid.json["id"]).first().is_valid == False
    assert session.query(Search).filter(Search.id==admin_filter_set_post_real.json["id"]).first().is_valid
    assert session.query(Search).filter(Search.id==admin_filter_set_post_invalid.json["id"]).first().is_valid == False
    assert session.query(Search).filter(Search.id==admin_copy_search_to_user_post_real.json["id"]).first().is_valid
    assert session.query(Search).filter(Search.id==admin_copy_search_to_user_post_invalid.json["id"]).first().is_valid == False
    assert session.query(Search).filter(Search.id==filter_set_post_invalid_for_portal_valid_for_data_dictionary.json["id"]).first().is_valid == False
    assert session.query(Search).filter(Search.id==filter_set_post_malformed.json["id"]).first().is_valid == False
    assert session.query(Search).filter(Search.id==filter_set_no_graphql_object.json["id"]).first().is_valid == False
    session.refresh(filter_set_no_filter_source)
    assert filter_set_no_filter_source.is_valid == False
    session.refresh(filter_set_no_filter_source_internal_id)
    assert filter_set_no_filter_source_internal_id.is_valid == False
    
    assert session.query(SearchIsShared).filter(SearchIsShared.shareable_token == filter_set_snapshot_post_real.json).first().search.is_valid
    assert session.query(SearchIsShared).filter(SearchIsShared.shareable_token == filter_set_snapshot_post_invalid.json).first().search.is_valid == False

    assert session.query(Project).filter(Project.id==project_post_real.json["id"]).first().searches[0].is_valid
    assert session.query(Project).filter(Project.id==project_post_invalid.json["id"]).first().searches[0].is_valid == False

pytest.mark.order(9)
def test_manual_change_to_filter_set_auto_updates_is_valid(session, register_user, login, filter_set_post, filter_set_put, pytestconfig):
    user_id, user_email = register_user(email=f"user_1@test_manual_change_to_filter_set_auto_updates_is_valid.com", name="test_manual_change_to_filter_set_auto_updates_is_valid")
    
    fake_graphql_object = {"AND":[{"NOT_REAL":{"consortium":["INRG"]}}]}
    real_graphql_object = {"AND":[{"IN":{"consortium":["INRG"]}}]}

    login(user_id, user_email)
    filter_set_post_invalid_1 = filter_set_post(
        user_id,
        name="invalid_filter_set_from_filter_set_post",
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
        graphql_object=fake_graphql_object,
        description="invalid_filter_set_from_filter_set_post",
    )
    
    filter_set_post_invalid_2 = filter_set_post(
        user_id,
        name="invalid_filter_set_from_filter_set_post",
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
        graphql_object=fake_graphql_object,
        description="invalid_filter_set_from_filter_set_post",
    )
    
    main(["--file_name", pytestconfig.getoption("--configuration-file")])

    assert session.query(Search).filter(Search.id==filter_set_post_invalid_1.json["id"]).first().is_valid == False
    assert session.query(Search).filter(Search.id==filter_set_post_invalid_2.json["id"]).first().is_valid == False

    filter_set_put(
        user_id,
        filter_set_id=filter_set_post_invalid_1.json["id"],
        graphql_object=real_graphql_object,
    )

    filter_set_put(
        user_id,
        filter_set_id=filter_set_post_invalid_2.json["id"],
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
    )

    assert session.query(Search).filter(Search.id==filter_set_post_invalid_1.json["id"]).first().is_valid
    assert session.query(Search).filter(Search.id==filter_set_post_invalid_2.json["id"]).first().is_valid


pytest.mark.order(10)
def test_manual_change_to_filter_set_does_not_update_is_valid(session, register_user, login, filter_set_post, filter_set_put, pytestconfig):
    user_id, user_email = register_user(email=f"user_1@test_manual_change_to_filter_set_does_not_update_is_valid.com", name="test_manual_change_to_filter_set_does_not_update_is_valid")
    
    fake_graphql_object = {"AND":[{"NOT_REAL":{"consortium":["INRG"]}}]}
    real_graphql_object = {"AND":[{"IN":{"consortium":["INRG"]}}]}

    login(user_id, user_email)

    filter_set_post_invalid_1 = filter_set_post(
        user_id,
        name="invalid_filter_set_from_filter_set_post",
        filter_object={"__combineMode":"AND","__type":"STANDARD","value":{"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}},
        graphql_object=fake_graphql_object,
        description="invalid_filter_set_from_filter_set_post",
    )
    
    main(["--file_name", pytestconfig.getoption("--configuration-file")])

    assert session.query(Search).filter(Search.id==filter_set_post_invalid_1.json["id"]).first().is_valid == False

    filter_set_put(
        user_id,
        filter_set_id=filter_set_post_invalid_1.json["id"],
        description="new description",
    )

    assert session.query(Search).filter(Search.id==filter_set_post_invalid_1.json["id"]).first().is_valid == False


pytest.mark.order(11)
def test_filter_set_invalid_list_manual_mark_as_invalid(session,  
                           pytestconfig,
                           filter_set_post, 
                           register_user,
                           login,
                           ):

    #generate bad filter set with filter_set_post
    user_id, user_email = register_user(email=f"user_1@test_filter_set_invalid_list_manual_mark_as_invalid.com", name="test_filter_set_invalid_list_manual_mark_as_invalid")
    real_graphql_object = {"AND":[{"IN":{"consortium":["INRG"]}}]}
    bad_filter_object = {"consortium":{"__type":"OPTION","selectedValues":["INRG"],"isExclusion":False}}
    login(user_id, user_email)
    filter_set_post_invalid_id = filter_set_post(
        user_id,
        name="invalid_filter_set_from_filter_set_post",
        filter_object=bad_filter_object,
        graphql_object=real_graphql_object,
        description="invalid_filter_set_from_filter_set_post",
    ).json["id"]
    #generate a json file with a list [] containing the id of the filter set and save that file to ~/.gen3/amanuensis/invalid-filters.json

    filter_set_invalid_list = [filter_set_post_invalid_id]
    invalid_filters_file = os.path.expanduser("~/.gen3/amanuensis/invalid-filters.json")
    if os.path.exists(invalid_filters_file):
        os.remove(invalid_filters_file)

    with open(invalid_filters_file, "w") as f:
        f.write(json.dumps(filter_set_invalid_list))


    main(["--file_name", pytestconfig.getoption("--configuration-file")])
    assert session.query(Search).filter(Search.id==filter_set_post_invalid_id).first().is_valid == False
    