import pytest
from alembic.config import main as alembic_main
from cdislogging import get_logger
from amanuensis.models import Search

logger = get_logger(__name__)


def test_update_filters_from_old_version(session):
     
    
    alembic_main(["--raiseerr", "upgrade", "head"])
    logger.info("Upgrading to the top")

    alembic_main(["--raiseerr", "downgrade", "c6059263d6b9"])
    logger.info("Downgrading to c6059263d6b9")

    # empty filter set
    search_1 = Search(name=f"test_update_filters_from_old_version-empty-filter-set")

    #double option
    search_2 = Search(name=f"test_update_filters_from_old_version-old_version_two_options",
           filter_object={"sex": {"selectedValues": ["Female"]}, "consortium": {"selectedValues": ["INSTRuCT"]}}
    )

    #single option
    search_3 = Search(name=f"test_update_filters_from_old_version-old_version_one_option",
           filter_object={"sex": {"selectedValues": ["Male", "Female"]}}
    )

    #combined mode present with or and range
    search_4 = Search(name=f"test_update_filters_from_old_version-old_version_range_filter_combined_mode_present",
           filter_object={"sex": {"selectedValues": ["Male"]}, "__combineMode": "OR", "age_at_censor_status": {"lowerBound": 6479, "upperBound": 10268}}
    )

    #anchored combined mode present with and
    search_5 = Search(name="test_update_filters_from_old_version-old_version_anchor_filter_combined_mode_present",
           filter_object={"sex": {"selectedValues": ["Male"]}, "race": {"selectedValues": ["Asian"]}, "__combineMode": "AND", "disease_phase:Initial Diagnosis": {"filter": {"tumor_assessments.tumor_classification": {"selectedValues": ["Primary"]}}}})       
    
    search_6 = Search(name="test_update_filters_from_old_version-normal_filter_set",
                      filter_object={"value": {"sex": {"__type": "OPTION", "selectedValues": ["Male"]}, "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INTERACT"]}}, "__type": "STANDARD", "__combineMode": "AND"}
    )

    # test one that is malformed
    search_7 = Search(name=f"test_update_filters_from_old_version-old_version_two_options",
           filter_object={"sex": {"selectedValues": ["Female"]}, "consortium": {"selectedValuess": ["INSTRuCT"]}}
    )
    
    session.add_all([search_1, search_2, search_3, search_4, search_5, search_6, search_7])
    session.commit()

    alembic_main(["--raiseerr", "upgrade", "head"])

    session.refresh(search_1)
    session.refresh(search_2)
    session.refresh(search_3)
    session.refresh(search_4)
    session.refresh(search_5)
    session.refresh(search_6)
    session.refresh(search_7)

    assert search_1.filter_object == {}
    assert search_2.filter_object == {"__combineMode": "AND", "__type": 'STANDARD', "value": {"sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Female"]}, "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INSTRuCT"]}}}
    assert search_3.filter_object == {"__combineMode": "AND", "__type": 'STANDARD', "value": {"sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male", "Female"]}}}
    assert search_4.filter_object == {"__combineMode": "OR", "__type": 'STANDARD', "value": {"sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male"]}, "age_at_censor_status": {"__type": "RANGE", "lowerBound": 6479, "upperBound": 10268}}}
    assert search_5.filter_object == {"__combineMode": "AND", "__type": 'STANDARD', "value": {"sex": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Male"]}, "race": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Asian"]}, "disease_phase:Initial Diagnosis": {"__type": "ANCHOR", "value": {"tumor_assessments.tumor_classification": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["Primary"]}}}}}
    assert search_6.filter_object == {"value": {"sex": {"__type": "OPTION", "selectedValues": ["Male"]}, "consortium": {"__type": "OPTION", "isExclusion": False, "selectedValues": ["INTERACT"]}}, "__type": "STANDARD", "__combineMode": "AND"}
    assert search_7.filter_object == {"sex": {"selectedValues": ["Female"]}, "consortium": {"selectedValuess": ["INSTRuCT"]}}