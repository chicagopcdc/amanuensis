import pytest
from amanuensis.resources.filter_sets import _load_data_files, _retrieve_data_dictionary, _get_explorer_selectable_values, _check_es_to_dd_map, _check_portal_config, check_filter_sets 
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

@pytest.fixture(scope="module")
def data_dictionary():
    data_dictionary = _retrieve_data_dictionary()
    yield data_dictionary



pytest.mark.order(1)
def test__load_data_files():
    assert _load_data_files("es_to_dd_map.json")
    assert _load_data_files("gitops.json")
    with pytest.raises(NotFound):
        _load_data_files("not_real.json")

pytest.mark.order(2)
def test__retrieve_data_dictionary():
    assert _retrieve_data_dictionary()

pytest.mark.order(3)
def test__get_explorer_selectable_values(portal_config):
    assert _get_explorer_selectable_values(portal_config)

pytest.mark.order(4)
def test_check_portal_config(portal_config):
    selectable_values = _get_explorer_selectable_values(portal_config)


    valid_filter_set = Search(
        name="valid", 
        filter_object={
            "value": {
                "sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male"]}, 
                "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}
            }, 
            "__type": "STANDARD", 
            "__combineMode": "AND"
        }
    )

    assert _check_portal_config(valid_filter_set, selectable_values)

    #test that the selected value "invalid" is not valid
    invalid_filter_set = Search(
            name="invalid", 
            filter_object={
                "value": {
                    "sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male"]}, 
                    "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]},
                    "invalid": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["NOT_REAL"]}
                }, 
                "__type": "STANDARD", 
                "__combineMode": "AND"
            }
        )

    assert not _check_portal_config(invalid_filter_set, selectable_values)

pytest.mark.order(5)
def test_check_es_to_dd_map(es_to_dd_map, data_dictionary):
    valid_filter_set = Search(
        name="In_valid", 
        filter_object={
            "value": {
                "sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male"]}, 
                "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}, #enum
                "studies.treatment_arm": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}, #array
                "tumor_assessments.longest_diam_dim1": {"__type": "RANGE", "lowerBound": 20, "upperBound": 76}
            }, 
            "__type": "STANDARD", 
            "__combineMode": "AND"
        }
    )

    assert _check_es_to_dd_map(valid_filter_set, es_to_dd_map, data_dictionary)

    invalid_filter_set_doesnt_exist_in_elastic_search = Search(
        name="In_valid", 
        filter_object={
            "value": {
                "sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male"]}, 
                "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}, #enum
                "studies.treatment_arm": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}, #array
                "tumor_assessments.longest_diam_dim1": {"__type": "RANGE", "lowerBound": 20, "upperBound": 76},
                "not_real": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}
            }, 
            "__type": "STANDARD", 
            "__combineMode": "AND"
        }
    )

    assert not _check_es_to_dd_map(invalid_filter_set_doesnt_exist_in_elastic_search, es_to_dd_map, data_dictionary)

    invalid_filter_set_doesnt_exist_in_dictionary = Search(
        name="In_valid", 
        filter_object={
            "value": {
                "sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male"]}, 
                "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}, #enum
                "studies.treatment_arm": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}, #array
                "tumor_assessments.longest_diam_dim1": {"__type": "RANGE", "lowerBound": 20, "upperBound": 76},
                "_molecular_analysis_count": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}
            }, 
            "__type": "STANDARD", 
            "__combineMode": "AND"
        }
    )

    assert not _check_es_to_dd_map(invalid_filter_set_doesnt_exist_in_dictionary, es_to_dd_map, data_dictionary)


    consortium = data_dictionary["subject"]["properties"]["consortium"]

    data_dictionary.pop("subject")

    with pytest.raises(InternalError):
        _check_es_to_dd_map(invalid_filter_set_doesnt_exist_in_dictionary, es_to_dd_map, data_dictionary)


    data_dictionary["subject"] = consortium


    #test filter is improperly formatted
    invalid_filter_set = Search(
        name="In_valid", 
        filter_object={
            "value": {
                "sex": {"isExclusion": False, "selectedValues": ["Male"]}, 
                "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}, #enum
                "studies.treatment_arm": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}, #array
                "tumor_assessments.longest_diam_dim1": {"__type": "RANGE", "lowerBound": 20, "upperBound": 76},
            }, 
            "__type": "STANDARD", 
            "__combineMode": "AND"
        }
    )

    assert not _check_es_to_dd_map(invalid_filter_set, es_to_dd_map, data_dictionary)

    #test filter is improperly formatted
    invalid_filter_set = Search(
        name="In_valid", 
        filter_object={
            "value": {
                "sex": {"__type": "OPTION", "isExclusion": False}, 
                "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}, #enum
                "studies.treatment_arm": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}, #array
                "tumor_assessments.longest_diam_dim1": {"__type": "RANGE", "lowerBound": 20, "upperBound": 76},
            }, 
            "__type": "STANDARD", 
            "__combineMode": "AND"
        }
    )

    assert not _check_es_to_dd_map(invalid_filter_set, es_to_dd_map, data_dictionary)


    #test filter has enum no longer supported 

    invalid_filter_set = Search(
        name="In_valid", 
        filter_object={
            "value": {
                "sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male", "NOT_REAL_VALUE"]}, 
                "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}, #enum
                "studies.treatment_arm": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}, #array
                "tumor_assessments.longest_diam_dim1": {"__type": "RANGE", "lowerBound": 20, "upperBound": 76},
            }, 
            "__type": "STANDARD", 
            "__combineMode": "AND"
        }
    )

    assert not _check_es_to_dd_map(invalid_filter_set, es_to_dd_map, data_dictionary)

pytest.mark.order(6)
def test_check_filter_sets(session, data_dictionary, es_to_dd_map):

    session.add_all([
        Search(
            name="In_valid", 
            filter_object={
                "value": {
                    "sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["NOT_REAL"]}, 
                    "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}, #enum
                    "studies.treatment_arm": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}, #array
                    "tumor_assessments.longest_diam_dim1": {"__type": "RANGE", "lowerBound": 20, "upperBound": 76},
                }, 
                "__type": "STANDARD", 
                "__combineMode": "AND"
            }
        ), 
        Search(
            name="valid",
            filter_object={
                "value": {
                    "sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male"]}, 
                    "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INRG"]}, #enum
                    "studies.treatment_arm": {"__type": "OPTION", "selectedValues": ["some study"], "isExclusion": False}, #array
                    "tumor_assessments.longest_diam_dim1": {"__type": "RANGE", "lowerBound": 20, "upperBound": 76},
                }, 
                "__type": "STANDARD", 
                "__combineMode": "AND"
            }
        )
    ])

    session.commit()

    check_filter_sets(session, es_to_dd_map_file_name="es_to_dd_map.json", portal_config_file_name="gitops.json")

    session.commit()

    for search in session.query(Search).all():

        if search.name == "In_valid":
            assert search.is_valid == False
        
        if search.name == "valid":
            assert search.is_valid == True

pytest.mark.order(7)
def test_using_script(session):
    session.query(Search)\
        .filter(Search.name == "In_valid")\
        .update({
            Search.filter_object: {
                "value": {
                    "sex": {
                        "__type": "OPTION", 
                        "isExclusion": False, 
                        "selectedValues": ["Male"]
                    }
                }, 
                "__type": "STANDARD", 
                "__combineMode": "AND"
            }
        })
    session.commit()
    
    main()


    update_valid_state = session.query(Search).filter(Search.name == "In_valid").first()

    assert update_valid_state.is_valid