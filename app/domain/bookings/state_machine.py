from enum import Enum
from app.core.exceptions import InvalidStateTransitionError

class BookingStatus(str, Enum):
    HELD = "held"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    BOARDED = "boarded"

_ALLOWED_TRANSITIONS = {
    BookingStatus.HELD: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.EXPIRED},
    BookingStatus.CONFIRMED: {BookingStatus.BOARDED, BookingStatus.CANCELLED},
    BookingStatus.CANCELLED: set(),
    BookingStatus.EXPIRED: set(),
    BookingStatus.BOARDED: set(),
}

def validate_transition(current: BookingStatus, next: BookingStatus):
    if next not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidStateTransitionError(f"Cannot transition booking from {current} to {next}")
