import asyncio
import logging
from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.domain.bookings.models import BookingORM, BookingStatus
from app.domain.bookings.repository import BookingRepository
from app.domain.trips.repository import TripRepository

logger = logging.getLogger("workers")

async def expire_old_bookings():
    """Worker task to clean up expired bookings."""
    logger.info("Running booking expiration worker...")
    
    session_factory = get_session_factory()
    booking_repository = BookingRepository(session=session_factory(), trip_repository=TripRepository(session=session_factory()))
    
    now = datetime.now(UTC)
    
    # Query for HELD bookings where hold_expires_at is in the past
    expired_bookings_query = (
        session_factory()
        .query(BookingORM)
        .filter(
            BookingORM.booking_state == BookingStatus.HELD,
            BookingORM.hold_expires_at < now,
        )
        .all()
    )
    
    if not expired_bookings_query:
        logger.info("No expired bookings found.")
        return

    logger.info(f"Found {len(expired_bookings_query)} expired bookings.")
    
    for booking in expired_bookings_query:
        try:
            # Calling get() triggers the expiry logic via BookingPolicy.ensure_booking_is_active
            # which handles state transition and seat restoration.
            booking_repository.get(booking.id)
            logger.info(f"Expired booking: {booking.id}")
        except Exception as e:
            logger.error(f"Failed to expire booking {booking.id}: {e}")
    
    logger.info("Booking expiration complete.")
