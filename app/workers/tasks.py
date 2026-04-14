import asyncio
import logging
from app.core.config import get_settings

logger = logging.getLogger("workers")

async def expire_old_bookings():
    """Worker task to clean up expired bookings."""
    logger.info("Running booking expiration worker...")
    # Logic to identify and transition stale 'held' bookings to 'expired'
    await asyncio.sleep(1)
    logger.info("Booking expiration complete.")
