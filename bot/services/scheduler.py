from __future__ import annotations

import asyncio
import logging

from bot.services.database import db, getSecondsUntilMidnightIst

logger = logging.getLogger(__name__)


async def midnightResetLoop() -> None:
    """Runs forever. Waits until midnight IST then resets all daily counters."""
    while True:
        secondsUntilMidnight = getSecondsUntilMidnightIst()
        logger.info(f"Next daily reset in {secondsUntilMidnight:.0f}s ({secondsUntilMidnight/3600:.2f}h)")
        await asyncio.sleep(secondsUntilMidnight + 5)  # +5s buffer past midnight
        db.resetAllTests()
        logger.info("Daily test counters reset for all users.")
