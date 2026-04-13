from datetime import UTC, datetime

from app.domain.bookings.models import BookingORM


class BookingPolicy:
    @staticmethod
    def ensure_booking_is_active(booking: BookingORM) -> BookingORM:
        hold_expires_at = booking.hold_expires_at
        if hold_expires_at.tzinfo is None:
            hold_expires_at = hold_expires_at.replace(tzinfo=UTC)
        if (
            booking.booking_state == "held"
            and hold_expires_at <= datetime.now(UTC)
        ):
            booking.booking_state = "expired"
        return booking
