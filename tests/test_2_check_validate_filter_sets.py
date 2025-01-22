import pytest
from amanuensis.resources.filter_sets import _load_data_files, _get_selectable_filters_from_data_portal, _check_es_to_dd_map, _check_portal_config, check_filter_sets, _extract_selected_values_from_filter_set
from amanuensis.errors import NotFound, InternalError
from amanuensis.models import Search
from amanuensis.scripting.validate_filter_sets import main


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
    with pytest.raises(NotFound):
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
def test_check_filter_sets(session, es_to_dd_map):

    session.add_all([
        Search(
            name="valid_1", 
            graphql_object={"AND":[{"IN":{"consortium":["INRG"]}}]},
            filter_source_internal_id=1
        ), 
        Search(
            name="valid_2",
            graphql_object={
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
                        },
            filter_source_internal_id=1
        ),
        Search(
            name="valid_3",
            graphql_object={
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
            },
            filter_source_internal_id=1
        ),
        Search(
            name="valid_4",
            graphql_object= {
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
            },
            filter_source_internal_id=1
        ),
        Search(
            name="invalid_1",
            graphql_object={"AND":[{"NOT_REAL":{"consortium":["INRG"]}}]},
            filter_source_internal_id=1
        ),
        Search(
            name="invalid_2",
            graphql_object={
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
            },
            filter_source_internal_id=1
        ),

    ])

    session.commit()

    check_filter_sets(session, es_to_dd_map_file_name="es_to_dd_map.json", portal_config_file_name="gitops.json")

    session.commit()

    for search in session.query(Search).all():

        if search.name == "valid_1":
            assert search.is_valid == True
        
        if search.name == "valid_2":
            assert search.is_valid == True
        
        if search.name == "valid_3":
            assert search.is_valid == True
        
        if search.name == "valid_4":
            assert search.is_valid == True
        
        if search.name == "invalid_1":
            assert search.is_valid == False
        
        if search.name == "invalid_2":
            assert search.is_valid == False

pytest.mark.order(8)
def test_using_script(session, pytestconfig):
    session.query(Search)\
        .filter(Search.name == "invalid_1")\
        .update({
            Search.graphql_object: {"AND":[{"IN":{"consortium":["INRG"]}}]}
        })
    session.commit()
    
    main(pytestconfig.getoption("--configuration-file"))


    update_valid_state = session.query(Search).filter(Search.name == "invalid_1").first()

    assert update_valid_state.is_valid

pytest.mark.order(9)
def test_manual_change_to_filter_set_auto_updates_is_valid(session, register_user, client, login):
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    
    search = Search(
                graphql_object={"AND":[{"NOT_REAL":{"consortium":["INRG"]}}]},
                filter_source_internal_id=1,
                user_id=user_id,
                is_valid=False,
                filter_source="explorer"
            )
    session.add(
        search
    )
    session.commit()

    assert search.is_valid == False
    login(user_id, user_email)
    filter_set_update_json = {
        "name": "new_name",
        "description": "new_description",
    }
    filter_set_put_response = client.put(f'/filter-sets/{search.id}', json=filter_set_update_json, headers={"Authorization": f'bearer {user_id}'})
    assert filter_set_put_response.status_code == 200

    session.refresh(search)
    assert search.is_valid == False

    filter_set_update_json = {
        "gqlFilter": {"AND":[{"IN":{"consortium":["INRG"]}}]},
    }
    filter_set_put_response = client.put(f'/filter-sets/{search.id}', json=filter_set_update_json, headers={"Authorization": f'bearer {user_id}'})
    assert filter_set_put_response.status_code == 200

    session.refresh(search)
    assert search.is_valid