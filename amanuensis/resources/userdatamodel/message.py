from cdislogging import get_logger
from amanuensis.models import (
    Message,
)
from amanuensis.errors import NotFound, UserError
from amanuensis.models import Message

logger = get_logger(__name__)


def get_messages(current_session, sender_id=None, request_id=None, many=True, throw_not_found=False):

    logger.info(f"get_messages: {locals()}")

    messages = current_session.query(Message)

    if sender_id:
        messages = messages.filter(Message.sender_id == sender_id)

    if request_id:
        messages = messages.filter(Message.request_id == request_id)

    messages = messages.all()

    if not messages and throw_not_found:
        raise NotFound("No messages found")

    if not many:
        if len(messages) > 1:
            raise UserError("Multiple messages found")
        else:
            messages = messages[0] if messages else None

    return messages

def create_message(current_session, sender_id, request_id, body, sender_source=None):
    
    message = Message(
        sender_id=sender_id,
        request_id=request_id,
        body=body,
        sender_source=sender_source,
    )

    current_session.add(message)

    current_session.flush()

    return message

