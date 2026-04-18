from app.core.exceptions import InvalidStateTransitionError

_ALLOWED_TRANSITIONS = {
    "issued": {"assigned", "cancelled", "expired"},
    "assigned": {"boarded", "cancelled", "expired"},
    "boarded": set(),
    "cancelled": set(),
    "expired": set(),
}


def validate_transition(current: str, next_state: str) -> None:
    current_state = str(current)
    if next_state not in _ALLOWED_TRANSITIONS.get(current_state, set()):
        raise InvalidStateTransitionError(
            f"Cannot transition rank ticket from {current_state} to {next_state}"
        )
