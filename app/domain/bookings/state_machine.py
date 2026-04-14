from app.core.exceptions import InvalidStateTransitionError
from app.domain.bookings.models import BookingStatus

_ALLOWED_TRANSITIONS = {
    BookingStatus.HELD: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.EXPIRED},
    BookingStatus.CONFIRMED: {BookingStatus.BOARDED, BookingStatus.CANCELLED},
    BookingStatus.CANCELLED: set(),
    BookingStatus.EXPIRED: set(),
    BookingStatus.BOARDED: set(),
}


def validate_transition(current: BookingStatus | str, next: BookingStatus) -> None:
    current_state = BookingStatus(current)
    if next not in _ALLOWED_TRANSITIONS.get(current_state, set()):
        raise InvalidStateTransitionError(
            f"Cannot transition booking from {current_state.value} to {next.value}"
        )
