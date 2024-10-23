import pytest


from amanuensis.errors import InternalError
from amanuensis.resources.request import calculate_overall_project_state as get_overall_project_state
from amanuensis import app
#from amanuensis.errors import InternalError 

#test errors

def test_incorrect_data(session):
    with app.app_context():
        with pytest.raises(InternalError) as e:
            state = {"NOT_A_VALID_STATE"}
            result = get_overall_project_state(session, this_project_requests_states=state)

        assert str(e.value) == "[500] - Unable to load or find the consortium status"

def test_correct_and_incorrect_data(session):
    with app.app_context():
        with pytest.raises(InternalError) as e:
            state = {"SUBMITTED", "NOT_A_VALID_STATE"}
            result = get_overall_project_state(session, this_project_requests_states=state)

        assert str(e.value) == "[500] - Unable to load or find the consortium status"

def test_no_data(session):
    with app.app_context():
        result = get_overall_project_state(session, this_project_requests_states={})
        # assert result == {"status": None}
        project_status = result['status'] if result['status'] else "ERROR"
        assert project_status == "ERROR"


#test correctness

def test_published(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"PUBLISHED"}) == {"status": "PUBLISHED"}

def test_data_downloaded(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"PUBLISHED", "DATA_DOWNLOADED"}) == {"status": "PUBLISHED"}

def test_data_availble(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={ "DATA_DOWNLOADED", "DATA_AVAILABLE"}) == {"status": "DATA_AVAILABLE"}

def test_aggrements_executed(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={ "DATA_DOWNLOADED", "DATA_AVAILABLE", "AGREEMENTS_EXECUTED"}) == {"status": "AGREEMENTS_EXECUTED"}

def test_aggrements_negociated(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"DATA_DOWNLOADED", "DATA_AVAILABLE", 
                                      "AGREEMENTS_EXECUTED", "AGREEMENTS_NEGOTIATION"}) == {"status": "AGREEMENTS_NEGOTIATION"}

def test_request_critiera_finilized(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"DATA_DOWNLOADED", "DATA_AVAILABLE", 
                                        "AGREEMENTS_EXECUTED", "AGREEMENTS_NEGOTIATION",
                                        "REQUEST_CRITERIA_FINALIZED"}) == {"status": "REQUEST_CRITERIA_FINALIZED"}   

def test_submitted_revision_joint_1(session):
    with app.app_context():
        result = get_overall_project_state(session, this_project_requests_states={"SUBMITTED", "REVISION", "APPROVED", "APPROVED_WITH_FEEDBACK"})
        assert result == {"status": "SUBMITTED"}

def test_submitted_revision_joint_2(session):
    with app.app_context():
        result = get_overall_project_state(session, this_project_requests_states={"SUBMITTED", "REVISION", "APPROVED"})
        assert result == {"status": "SUBMITTED"}

def test_submitted_revision_joint_3(session):
    with app.app_context():
        result = get_overall_project_state(session, this_project_requests_states={"SUBMITTED", "REVISION", "APPROVED_WITH_FEEDBACK"})
        assert result == {"status": "SUBMITTED"}


def test_tie_approved(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"APPROVED_WITH_FEEDBACK", "APPROVED", "AGREEMENTS_NEGOTIATION"}) == {"status": "APPROVED_WITH_FEEDBACK"}


def test_tie_review(session):
    with app.app_context():    
        assert get_overall_project_state(session, this_project_requests_states={"APPROVED", "REVISION", "IN_REVIEW"}) == {"status": "REVISION"}

def test_tie_draft(session):
    with app.app_context():
        result = get_overall_project_state(session, this_project_requests_states={"DRAFT", "SUBMITTED", "REVISION", "APPROVED", "APPROVED_WITH_FEEDBACK"})
        assert result == {"status": "DRAFT"}



#test auto sinks

def test_Reject(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"APPROVED", "REVISION", "IN_REVIEW", "REJECTED"}) == {"status": "REJECTED"}

def test_Reject_pub(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"APPROVED", "REVISION", "IN_REVIEW", "REJECTED", "PUBLISHED"})["status"] in {"PUBLISHED", "REJECTED"}

def test_withdrawl(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"APPROVED", "REVISION", "IN_REVIEW", "WITHDRAWAL"}) == {"status": "WITHDRAWAL"}

def test_reject_withdrawl(session):
    with app.app_context():
        assert get_overall_project_state(session, this_project_requests_states={"WITHDRAWAL", "REJECTED"})["status"] in {"REJECTED", "WITHDRAWAL"}