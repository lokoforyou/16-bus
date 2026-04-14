from enum import Enum
from app.core.exceptions import InvalidStateTransitionError

class TripStatus(str, Enum):
    PLANNED = "planned"
    BOARDING = "boarding"
    ENROUTE = "enroute"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

_ALLOWED_TRANSITIONS = {
    TripStatus.PLANNED: {TripStatus.BOARDING, TripStatus.CANCELLED},
    TripStatus.BOARDING: {TripStatus.ENROUTE, TripStatus.CANCELLED},
    TripStatus.ENROUTE: {TripStatus.COMPLETED},
    TripStatus.COMPLETED: set(),
    TripStatus.CANCELLED: set(),
}

def validate_transition(current: TripStatus, next: TripStatus):
    if next not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidStateTransitionError(f"Cannot transition from {current} to {next}")
