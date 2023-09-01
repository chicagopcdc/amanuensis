import pytest

from amanuensis.blueprints.project import determine_status_code
from amanuensis.errors import InternalError

#test = print(determine_status_code({}))


def test_no_data():
    with pytest.raises(InternalError) as e:
        result = determine_status_code({})
    assert str(e.value) == "[500] - Unable to load or find the consortium status"


def test_incorrect_data():
    with pytest.raises(InternalError) as e:
        state = {"NOT_A_VALID_STATE"}
        result = determine_status_code(state)
    
    assert str(e.value) == "[500] - Unable to load or find the consortium status"

def test_correct_and_incorrect_data():
    with pytest.raises(InternalError) as e:
        state = {"SUBMITTED", "NOT_A_VALID_STATE"}
        result = determine_status_code(state)
    
    assert str(e.value) == "[500] - Unable to load or find the consortium status"

def test_simple_example():
    result = determine_status_code({"SUBMITTED", "REVISION", "APPROVED"})
    assert result == {"status": "SUBMITTED"}

def test_tie_approved():
    assert determine_status_code({"APPROVED_WITH_FEEDBACK", "APPROVED", "AGREEMENTS_NEGOTIATION"}) == {"status": "APPROVED_WITH_FEEDBACK"}


def test_tie_review():
    assert determine_status_code({"APPROVED", "REVISION", "IN_REVIEW"}) == {"status": "REVISION"}


def test_Reject():
    assert determine_status_code({"APPROVED", "REVISION", "IN_REVIEW", "REJECTED"}) == {"status": "REJECTED"}


def test_withdrawl():
    assert determine_status_code({"APPROVED", "REVISION", "IN_REVIEW", "WITHDRAWAL"}) == {"status": "WITHDRAWAL"}

def test_reject_withdrawl():
    assert determine_status_code({"WITHDRAWAL", "REJECTED"}) == {"status": "WITHDRAWAL"}

def test_data_downloaded():
    assert determine_status_code({"DATA_DOWNLOADED"}) == {"status": "DATA_DOWNLOADED"}