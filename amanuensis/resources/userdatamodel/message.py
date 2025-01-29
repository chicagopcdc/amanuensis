from flask import current_app
from sqlalchemy import func
from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Message,
)

# do this until AWS-related requests is handled by it's own project
from pcdcutils.environment import is_env_enabled

logger = get_logger(__name__)

__all__ = [
    "get_all_messages",
    "get_messages_by_request",
    "send_message",
]


def get_all_messages(current_session, logged_user_id):
    messages = current_session.query(Message).filter_by(sender_id=logged_user_id).all()
    return messages

def get_messages_by_request(current_session, logged_user_id, request_id):
    # messages = current_session.query(Message).filter(Message.sender_id == logged_user_id, Message.request_id == request_id).all()
    messages = (
        current_session.query(Message).filter(Message.request_id == request_id).all()
    )
    return messages


def send_message(
    current_session, logged_user_id, request_id, subject, body, receivers, emails
):
    """store message in db and send message to emails via aws ses"""
    new_message = Message(sender_id=logged_user_id, body=body, request_id=request_id)
    if receivers:
        new_message.receivers.extend(receivers)

    if is_env_enabled("SEND_MESSAGE_DEBUG"):
        # logger.debug(f"send_message receivers (debug mode): {str(receivers)}")
        logger.debug(f"send_message receivers (debug mode)")
    else:
        if receivers:
            current_session.add(new_message)
            current_session.flush()

    if is_env_enabled("AWS_SES_DEBUG"):
        logger.debug(f"send_message emails (debug mode): {str(emails)}")
    elif emails:
        # Send the Message via AWS SES
        return current_app.ses_boto.send_email_ses(body, emails, subject)

    return new_message