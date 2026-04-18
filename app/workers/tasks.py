from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.core.database import get_session_factory
from app.domain.bookings.models import BookingORM, BookingStatus
from app.domain.bookings.repository import BookingRepository
from app.domain.events import DomainEventName
from app.domain.trips.repository import TripRepository

logger = logging.getLogger("workers")


def handle_event(event) -> dict[str, str]:
    name = getattr(event, "name", "")
    payload = getattr(event, "payload", {})
    if name in {
        DomainEventName.BOOKING_HELD.value,
        DomainEventName.BOOKING_CONFIRMED.value,
        DomainEventName.BOOKING_CANCELLED.value,
        DomainEventName.BOOKING_BOARDED.value,
        DomainEventName.TRIP_CREATED.value,
        DomainEventName.TRIP_STATE_CHANGED.value,
        DomainEventName.TRIP_STARTED.value,
        DomainEventName.TRIP_DEPARTED.value,
        DomainEventName.RANK_TICKET_ISSUED.value,
        DomainEventName.RANK_TICKET_ASSIGNED.value,
        DomainEventName.RANK_TICKET_BOARDED.value,
        DomainEventName.PAYMENT_COMPLETED.value,
        DomainEventName.CASH_BOOKING_AUTHORIZED.value,
    }:
        logger.info("Handled event %s", name)
        return {"status": "handled", "event": name, "booking_id": str(payload.get("booking_id", ""))}
    logger.info("Ignored event %s", name)
    return {"status": "ignored", "event": name}


def expire_old_bookings() -> int:
    logger.info("Running booking expiration worker...")
    session = get_session_factory()()
    booking_repository = BookingRepository(session=session)
    trip_repository = TripRepository(session=session)
    expired = 0
    now = datetime.now(UTC)
    try:
        expired_bookings = session.query(BookingORM).filter(
            BookingORM.booking_state == BookingStatus.HELD.value,
            BookingORM.hold_expires_at < now,
        ).all()
        for booking in expired_bookings:
            trip = trip_repository.get_trip_for_update(booking.trip_id)
            if trip is None:
                continue
            booking.booking_state = BookingStatus.EXPIRED.value
            trip.seats_free = min(trip.seats_total, trip.seats_free + booking.party_size)
            trip_repository.update(trip)
            booking_repository.update(booking)
            expired += 1
        session.commit()
        logger.info("Expired %s bookings", expired)
        return expired
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
