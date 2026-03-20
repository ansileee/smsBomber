from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime

from bot.services.database import db, IST, getSecondsUntilMidnightIst

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Midnight reset loop
# ---------------------------------------------------------------------------

async def midnightResetLoop() -> None:
    """Runs forever. Waits until midnight IST then resets all daily counters
    and runs auto-ban check."""
    while True:
        secondsUntilMidnight = getSecondsUntilMidnightIst()
        logger.info(f"Next daily reset in {secondsUntilMidnight:.0f}s ({secondsUntilMidnight/3600:.2f}h)")
        await asyncio.sleep(secondsUntilMidnight + 5)
        db.resetAllTests()
        logger.info("Daily test counters reset for all users.")
        await runAutoBanCheck()


# ---------------------------------------------------------------------------
# Auto-ban check
# ---------------------------------------------------------------------------

async def runAutoBanCheck() -> None:
    """
    Flag users who have hit their daily limit 3 days in a row.
    Sends admin a notification — does NOT auto-ban, just flags for review.
    Admin can then decide to ban or raise the limit.
    """
    try:
        flagged = db.getAbuseFlaggedUsers()
        if not flagged:
            return
        from bot.config import ADMIN_ID
        from aiogram import Bot
        from bot.config import BOT_TOKEN
        bot = Bot(token=BOT_TOKEN)
        lines = [f"<b>Abuse Check</b>\n\n{len(flagged)} users flagged:\n"]
        for u in flagged[:10]:
            name = u["firstName"] or "Unknown"
            un   = f"@{u['username']}" if u.get("username") else str(u["userId"])
            lines.append(
                f"{name}  {un}  —  "
                f"limit hit {u['limitHitStreak']} days in a row"
            )
        try:
            await bot.send_message(ADMIN_ID, "\n".join(lines), parse_mode="HTML")
        except Exception:
            pass
        await bot.session.close()
        logger.info(f"Auto-ban check: {len(flagged)} users flagged.")
    except Exception as e:
        logger.error(f"Auto-ban check error: {e}")


# ---------------------------------------------------------------------------
# Scheduled tests loop
# ---------------------------------------------------------------------------

async def scheduledTestsLoop(bot) -> None:
    """
    Checks every 30 seconds for scheduled tests that are due to run.
    Fires them off and notifies the user.
    """
    while True:
        await asyncio.sleep(30)
        try:
            due = db.getDueScheduledTests()
            for sched in due:
                asyncio.create_task(_fireScheduledTest(sched, bot))
        except Exception as e:
            logger.error(f"Scheduled tests loop error: {e}")


async def _fireScheduledTest(sched: dict, bot) -> None:
    """Launch a scheduled test for a user."""
    from bot.services.tester_runner import TesterRunner
    from bot.services.database import db

    userId   = sched["userId"]
    phone    = sched["phone"]
    duration = sched["duration"]
    workers  = sched["workers"]
    schedId  = sched["id"]

    # Mark as triggered so it doesn't fire again
    db.markScheduledTestTriggered(schedId)

    # Check if user can still run
    allowed, testsToday, dailyLimit = db.canRunTest(userId)
    if not allowed:
        try:
            await bot.send_message(
                userId,
                f"<b>Scheduled Test</b>\n\n"
                f"Could not run your scheduled test for <code>{phone}</code>.\n"
                f"Daily limit reached ({testsToday}/{dailyLimit}).",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    if db.isPhoneBlacklisted(phone):
        try:
            await bot.send_message(
                userId,
                f"<b>Scheduled Test</b>\n\n"
                f"Could not run — <code>{phone}</code> is now blacklisted.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    try:
        await bot.send_message(
            userId,
            f"<b>Scheduled Test Starting</b>\n\n"
            f"Phone    <code>{phone}</code>\n"
            f"Duration <code>{duration}s</code>\n"
            f"Workers  <code>{workers}</code>\n\n"
            f"<i>Test is running in the background. You will get a summary when it finishes.</i>",
            parse_mode="HTML"
        )
    except Exception:
        pass

    db.incrementTestCount(userId)
    recordId = db.startTestRecord(userId, phone, duration, workers)

    runner = TesterRunner(phone=phone, duration=duration, workers=workers, useProxy=False)
    await runner.start()

    # Wait for test to finish
    while runner.isRunning:
        await asyncio.sleep(2)

    snap      = runner.stats.snapshot()
    totalReqs = snap.get("totalReqs", 0)
    otpHits   = snap.get("confirmed", 0)

    # Build API snapshot
    apiSnapshot = json.dumps({
        name: {
            "confirmed": s.get("confirmed", 0),
            "requests":  s.get("requests", 0),
        }
        for name, s in snap.get("perApi", {}).items()
        if s.get("requests", 0) > 0
    })

    db.finishTestRecord(
        recordId=recordId,
        totalReqs=totalReqs,
        otpHits=otpHits,
        errors=snap["errors"],
        rps=snap["rps"],
        apiSnapshot=apiSnapshot,
    )
    db.updateUserStats(userId, totalReqs, otpHits)

    elapsed = int(snap["elapsed"])
    try:
        await bot.send_message(
            userId,
            f"<b>Scheduled Test Complete</b>\n\n"
            f"Phone      <code>{phone}</code>\n"
            f"Duration   <code>{elapsed}s</code>\n"
            f"Requests   <code>{totalReqs}</code>\n"
            f"OTPs       <code>{otpHits}</code>\n"
            f"Errors     <code>{snap['errors']}</code>\n"
            f"Req/sec    <code>{snap['rps']}</code>",
            parse_mode="HTML"
        )
    except Exception:
        pass