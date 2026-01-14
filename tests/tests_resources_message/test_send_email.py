from amanuensis.errors import InternalError, UserError
from amanuensis.resources.message import send_email
from cdislogging import get_logger
import ast
import pytest
from amanuensis.config import config
import flask
logger = get_logger(__name__)

def test_send_email(pytestconfig):
    
    if not pytestconfig.getoption("--test-emails-to-send-notifications"):
        logger.warning("Skipping test_upload_file_to_test_upload_file_to_project_and_then_send_email_successproject_success as no email to send notifications is provided will be marked as fail")
        assert False
    
    else:
        email_list = ast.literal_eval(pytestconfig.getoption("--test-emails-to-send-notifications")) if pytestconfig.getoption("--test-emails-to-send-notifications") else []


    send_email(subject="Test Email", body_text="test_send_email.", recipients=email_list)


def test_send_email_no_recipients():
    with pytest.raises(UserError):
        send_email(subject="Test Email", body_text="test_send_email_no_recipients.", recipients=[])


def test_send_email_no_sender(pytestconfig):
    # Temporarily modify the config to remove the sender
    original_sender = None
    if "SENDER" in config["AWS_CREDENTIALS"]["AWS_SES"]:
        original_sender = config["AWS_CREDENTIALS"]["AWS_SES"].pop("SENDER") 
    try:
        email_list = ast.literal_eval(pytestconfig.getoption("--test-emails-to-send-notifications")) if pytestconfig.getoption("--test-emails-to-send-notifications") else []
        with pytest.raises(InternalError):
            send_email(subject="Test Email", body_text="test_send_email_no_sender.", recipients=email_list)
    except Exception as e:
        assert False, f"Unexpected exception raised: {e}"
    finally:
        # Restore the original sender
        if original_sender:
            config["AWS_CREDENTIALS"]["AWS_SES"]["SENDER"] = original_sender

def test_send_email_no_ses_configured(pytestconfig):
    # Temporarily modify the app to remove ses_boto
    original_ses_boto = flask.current_app.ses_boto
    flask.current_app.ses_boto = None
    try:
        email_list = ast.literal_eval(pytestconfig.getoption("--test-emails-to-send-notifications")) if pytestconfig.getoption("--test-emails-to-send-notifications") else []
        with pytest.raises(InternalError):
            send_email(subject="Test Email", body_text="test_send_email_no_ses_configured.", recipients=email_list)
    except Exception as e:
        assert False, f"Unexpected exception raised: {e}"
    finally:
        # Restore the original ses_boto
        flask.current_app.ses_boto = original_ses_boto

def test_send_email_no_CC_recipients(pytestconfig):
    # Temporarily modify the config to remove the CC_RECIPIENTS
    original_cc_recipients = None
    if "CC_RECIPIENTS" in config["AWS_CREDENTIALS"]["AWS_SES"]:
        original_cc_recipients = config["AWS_CREDENTIALS"]["AWS_SES"].pop("CC_RECIPIENTS") 
    try:
        email_list = ast.literal_eval(pytestconfig.getoption("--test-emails-to-send-notifications")) if pytestconfig.getoption("--test-emails-to-send-notifications") else []
        send_email(subject="Test Email", body_text="test_send_email_no_CC_recipients.", recipients=email_list)
    except Exception as e:
        assert False, f"Unexpected exception raised: {e}"
    finally:
        # Restore the original CC_RECIPIENTS
        if original_cc_recipients:
            config["AWS_CREDENTIALS"]["AWS_SES"]["CC_RECIPIENTS"] = original_cc_recipients

def test_send_email_with_patch_running(patch_ses_client):
    with pytest.raises(InternalError):
        send_email(subject="Test Email", body_text="test_send_email_with_patch_running.", recipients=["test@example.com"])
    patch_ses_client()
    try:
        send_email(subject="Test Email", body_text="test_send_email_with_patch_running.", recipients=["test@example.com"])
    except Exception as e:
        assert False, f"Unexpected exception raised: {e}"