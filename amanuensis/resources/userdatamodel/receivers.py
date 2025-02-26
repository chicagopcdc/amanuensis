from amanuensis.models import Receiver
from cdislogging import get_logger
logger = get_logger(__name__)

def create_receiver(session, receiver_id, message_id):
    receiver = Receiver(receiver_id=receiver_id, message_id=message_id)
    session.add(receiver)
    session.flush()
    return receiver