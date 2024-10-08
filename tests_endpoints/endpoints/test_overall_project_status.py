import pytest


from amanuensis.errors import InternalError
from amanuensis.resources.project import get_overall_project_state
from amanuensis import app
#from amanuensis.errors import InternalError 

#test errors

def test_incorrect_data(client):
    with app.app_context():
        with pytest.raises(InternalError) as e:
            state = {"NOT_A_VALID_STATE"}
            result = get_overall_project_state(state)

        assert str(e.value) == "[500] - Unable to load or find the consortium status"

def test_correct_and_incorrect_data(client):
    with app.app_context():
        with pytest.raises(InternalError) as e:
            state = {"SUBMITTED", "NOT_A_VALID_STATE"}
            result = get_overall_project_state(state)

        assert str(e.value) == "[500] - Unable to load or find the consortium status"

def test_no_data(client):
    with app.app_context():
        result = get_overall_project_state({})
        # assert result == {"status": None}
        project_status = result['status'] if result['status'] else "ERROR"
        assert project_status == "ERROR"


#test correctness

def test_published(client):
    with app.app_context():
        assert get_overall_project_state({"PUBLISHED"}) == {"status": "PUBLISHED"}

def test_data_downloaded(client):
    with app.app_context():
        assert get_overall_project_state({"PUBLISHED", "DATA_DOWNLOADED"}) == {"status": "PUBLISHED"}

def test_data_availble(client):
    with app.app_context():
        assert get_overall_project_state({ "DATA_DOWNLOADED", "DATA_AVAILABLE"}) == {"status": "DATA_AVAILABLE"}

def test_aggrements_executed(client):
    with app.app_context():
        assert get_overall_project_state({ "DATA_DOWNLOADED", "DATA_AVAILABLE", "AGREEMENTS_EXECUTED"}) == {"status": "AGREEMENTS_EXECUTED"}

def test_aggrements_negociated(client):
    with app.app_context():
        assert get_overall_project_state({"DATA_DOWNLOADED", "DATA_AVAILABLE", 
                                      "AGREEMENTS_EXECUTED", "AGREEMENTS_NEGOTIATION"}) == {"status": "AGREEMENTS_NEGOTIATION"}

def test_request_critiera_finilized(client):
    with app.app_context():
        assert get_overall_project_state({"DATA_DOWNLOADED", "DATA_AVAILABLE", 
                                        "AGREEMENTS_EXECUTED", "AGREEMENTS_NEGOTIATION",
                                        "REQUEST_CRITERIA_FINALIZED"}) == {"status": "REQUEST_CRITERIA_FINALIZED"}   

def test_submitted_revision_joint_1(client):
    with app.app_context():
        result = get_overall_project_state({"SUBMITTED", "REVISION", "APPROVED", "APPROVED_WITH_FEEDBACK"})
        assert result == {"status": "SUBMITTED"}

def test_submitted_revision_joint_2(client):
    with app.app_context():
        result = get_overall_project_state({"SUBMITTED", "REVISION", "APPROVED"})
        assert result == {"status": "SUBMITTED"}

def test_submitted_revision_joint_3(client):
    with app.app_context():
        result = get_overall_project_state({"SUBMITTED", "REVISION", "APPROVED_WITH_FEEDBACK"})
        assert result == {"status": "SUBMITTED"}


def test_tie_approved(client):
    with app.app_context():
        assert get_overall_project_state({"APPROVED_WITH_FEEDBACK", "APPROVED", "AGREEMENTS_NEGOTIATION"}) == {"status": "APPROVED_WITH_FEEDBACK"}


def test_tie_review(client):
    with app.app_context():    
        assert get_overall_project_state({"APPROVED", "REVISION", "IN_REVIEW"}) == {"status": "REVISION"}

def test_tie_draft(client):
    with app.app_context():
        result = get_overall_project_state({"DRAFT", "SUBMITTED", "REVISION", "APPROVED", "APPROVED_WITH_FEEDBACK"})
        assert result == {"status": "DRAFT"}



#test auto sinks

def test_Reject(client):
    with app.app_context():
        assert get_overall_project_state({"APPROVED", "REVISION", "IN_REVIEW", "REJECTED"}) == {"status": "REJECTED"}

def test_Reject_pub(client):
    with app.app_context():
        assert get_overall_project_state({"APPROVED", "REVISION", "IN_REVIEW", "REJECTED", "PUBLISHED"})["status"] in {"PUBLISHED", "REJECTED"}

def test_withdrawl(client):
    with app.app_context():
        assert get_overall_project_state({"APPROVED", "REVISION", "IN_REVIEW", "WITHDRAWAL"}) == {"status": "WITHDRAWAL"}

def test_reject_withdrawl(client):
    with app.app_context():
        assert get_overall_project_state({"WITHDRAWAL", "REJECTED"})["status"] in {"REJECTED", "WITHDRAWAL"}