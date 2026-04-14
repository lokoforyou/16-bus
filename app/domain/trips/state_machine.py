from app.core.exceptions import InvalidStateTransitionError
from app.domain.trips.models import TripStatus

_ALLOWED_TRANSITIONS = {
    TripStatus.PLANNED: {TripStatus.BOARDING, TripStatus.CANCELLED},
    TripStatus.BOARDING: {TripStatus.ENROUTE, TripStatus.CANCELLED},
    TripStatus.ENROUTE: {TripStatus.COMPLETED},
    TripStatus.COMPLETED: set(),
    TripStatus.CANCELLED: set(),
}


def validate_transition(current: TripStatus | str, next: TripStatus) -> None:
    current_state = TripStatus(current)
    if next not in _ALLOWED_TRANSITIONS.get(current_state, set()):
        raise InvalidStateTransitionError(f"Cannot transition from {current_state.value} to {next.value}")
