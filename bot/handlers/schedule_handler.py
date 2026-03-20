from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.database import db, IST
from bot.config import ADMIN_ID, PROTECTED_NUMBER
from bot.utils import PM, b, i, c, hEsc

router = Router()

MAX_SCHEDULES_PER_USER = 3


class ScheduleStates(StatesGroup):
    phone    = State()
    duration = State()
    workers  = State()
    time     = State()


def parseTime(t: str) -> Optional[int]:
    t = (t or "").strip()
    try:
        if t.endswith("s"): return int(t[:-1])
        if t.endswith("m"): return int(t[:-1]) * 60
        if t.endswith("h"): return int(t[:-1]) * 3600
        return int(t)
    except (ValueError, AttributeError):
        return None


def parseScheduleTime(t: str) -> Optional[float]:
    """
    Parse a schedule time string into a UTC timestamp.
    Accepts:
      - HH:MM        (today in IST, or tomorrow if already past)
      - +30m / +2h   (relative from now)
    """
    t = (t or "").strip()
    now = datetime.now(IST)

    # Relative: +30m, +2h, +1h30m not supported, keep it simple
    if t.startswith("+"):
        secs = parseTime(t[1:])
        if secs and secs >= 60:
            return time.time() + secs
        return None

    # Absolute HH:MM
    try:
        parts = t.split(":")
        if len(parts) != 2:
            return None
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h < 24 and 0 <= m < 60):
            return None
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)  # schedule for tomorrow
        return target.timestamp()
    except Exception:
        return None


def formatRunAt(ts: float) -> str:
    dt = datetime.fromtimestamp(ts, tz=IST)
    now = datetime.now(IST)
    if dt.date() == now.date():
        return f"Today at {dt.strftime('%H:%M')} IST"
    elif dt.date() == (now + timedelta(days=1)).date():
        return f"Tomorrow at {dt.strftime('%H:%M')} IST"
    return dt.strftime("%d %b %H:%M IST")


def formatDuration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    m, s = seconds // 60, seconds % 60
    return f"{m}m {s}s" if s else f"{m}m"


# ---------------------------------------------------------------------------
# View scheduled tests
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:schedule")
async def cbScheduleMenu(callback: CallbackQuery) -> None:
    userId    = callback.from_user.id
    schedules = db.getScheduledTests(userId)
    builder   = InlineKeyboardBuilder()

    if schedules:
        for s in schedules:
            label = f"{s['phone']}  {formatRunAt(s['runAt'])}"
            builder.button(text=label,    callback_data=f"sched:cancel:{s['id']}")
        builder.adjust(1)

    if len(schedules) < MAX_SCHEDULES_PER_USER:
        builder.button(text="Schedule New Test", callback_data="sched:new")
    builder.button(text="Main Menu", callback_data="nav:main_menu")
    builder.adjust(1)

    text = f"{b('Scheduled Tests')}\n\n"
    if schedules:
        text += i("Tap a schedule to cancel it.\n\n")
        for s in schedules:
            text += (
                f"{c(s['phone'])}  {formatDuration(s['duration'])}  "
                f"{s['workers']} workers\n"
                f"{i(formatRunAt(s['runAt']))}\n\n"
            )
    else:
        text += i(f"No scheduled tests. You can schedule up to {MAX_SCHEDULES_PER_USER}.")

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=PM)
    await callback.answer()


@router.callback_query(F.data.startswith("sched:cancel:"))
async def cbCancelSchedule(callback: CallbackQuery) -> None:
    schedId = int(callback.data.split(":")[2])
    db.deleteScheduledTest(schedId, callback.from_user.id)
    await callback.answer("Schedule cancelled.")
    callback.data = "menu:schedule"
    await cbScheduleMenu(callback)


# ---------------------------------------------------------------------------
# Schedule new test wizard
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "sched:new")
async def cbScheduleNew(callback: CallbackQuery, state: FSMContext) -> None:
    userId    = callback.from_user.id
    schedules = db.getScheduledTests(userId)
    if len(schedules) >= MAX_SCHEDULES_PER_USER:
        await callback.answer(f"Max {MAX_SCHEDULES_PER_USER} schedules allowed.", show_alert=True)
        return
    await state.set_state(ScheduleStates.phone)
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="menu:schedule")

    # Offer favorites as quick pick
    favs = db.getFavorites(userId)
    if favs:
        for f in favs:
            label = f["label"] or f["phone"]
            builder.button(text=label, callback_data=f"sched:phone:{f['phone']}")
        builder.adjust(1)

    await callback.message.edit_text(
        f"{b('Schedule Test')}\n\nEnter the 10-digit target number.\n{i('Or pick a favorite below.')}",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sched:phone:"), StateFilter(ScheduleStates.phone))
async def cbSchedulePickFav(callback: CallbackQuery, state: FSMContext) -> None:
    phone = callback.data.split(":", 2)[2]
    await state.update_data(schedPhone=phone)
    await state.set_state(ScheduleStates.duration)
    builder = InlineKeyboardBuilder()
    for d in [("30s", 30), ("1 min", 60), ("5 min", 300), ("10 min", 600)]:
        builder.button(text=d[0], callback_data=f"sched:dur:{d[1]}")
    builder.button(text="Back", callback_data="sched:new")
    builder.adjust(4, 1)
    await callback.message.edit_text(
        f"{b('Schedule Test')}  {c(phone)}\n\nSelect duration.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.message(StateFilter(ScheduleStates.phone))
async def handleSchedPhone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if not phone.isdigit() or len(phone) != 10:
        await message.answer(f"{b('Invalid')}  Must be exactly 10 digits.", parse_mode=PM)
        return
    if phone == PROTECTED_NUMBER and message.from_user.id != ADMIN_ID:
        import random
        from bot.handlers.test_flow import PROTECTED_RESPONSES
        await message.answer(random.choice(PROTECTED_RESPONSES))
        return
    if db.isPhoneBlacklisted(phone) and message.from_user.id != ADMIN_ID:
        await message.answer("That number is not available for testing.")
        return
    await state.update_data(schedPhone=phone)
    await state.set_state(ScheduleStates.duration)
    builder = InlineKeyboardBuilder()
    for d in [("30s", 30), ("1 min", 60), ("5 min", 300), ("10 min", 600)]:
        builder.button(text=d[0], callback_data=f"sched:dur:{d[1]}")
    builder.adjust(4)
    await message.answer(
        f"{b('Schedule Test')}  {c(phone)}\n\nSelect duration.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )


@router.callback_query(F.data.startswith("sched:dur:"), StateFilter(ScheduleStates.duration))
async def cbSchedDuration(callback: CallbackQuery, state: FSMContext) -> None:
    duration = int(callback.data.split(":")[2])
    await state.update_data(schedDuration=duration)
    await state.set_state(ScheduleStates.workers)
    builder = InlineKeyboardBuilder()
    for w in [2, 4, 8, 16]:
        builder.button(text=str(w), callback_data=f"sched:wrk:{w}")
    builder.adjust(4)
    await callback.message.edit_text(
        f"{b('Schedule Test')}\n\nDuration {c(formatDuration(duration))}\n\nSelect workers.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sched:wrk:"), StateFilter(ScheduleStates.workers))
async def cbSchedWorkers(callback: CallbackQuery, state: FSMContext) -> None:
    workers = int(callback.data.split(":")[2])
    await state.update_data(schedWorkers=workers)
    await state.set_state(ScheduleStates.time)
    builder = InlineKeyboardBuilder()
    # Quick time options
    now = datetime.now(IST)
    for mins in [30, 60, 120]:
        t = (now + timedelta(minutes=mins)).strftime("%H:%M")
        builder.button(text=f"+{mins}m ({t})", callback_data=f"sched:at:+{mins}m")
    builder.button(text="Cancel", callback_data="menu:schedule")
    builder.adjust(3, 1)
    await callback.message.edit_text(
        f"{b('Schedule Test')}\n\nWorkers {c(str(workers))}\n\n"
        f"When should this test run?\n\n"
        f"Type a time: {c('22:30')} (IST) or relative: {c('+1h')} {c('+30m')}\n"
        f"{i('Or pick a quick option below.')}",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sched:at:"), StateFilter(ScheduleStates.time))
async def cbSchedQuickTime(callback: CallbackQuery, state: FSMContext) -> None:
    timeStr = callback.data.split(":", 2)[2]
    await _finalizeSchedule(callback.message, state, callback.from_user.id, timeStr, isCallback=True)
    await callback.answer()


@router.message(StateFilter(ScheduleStates.time))
async def handleSchedTime(message: Message, state: FSMContext) -> None:
    timeStr = (message.text or "").strip()
    await _finalizeSchedule(message, state, message.from_user.id, timeStr, isCallback=False)


async def _finalizeSchedule(msgOrCb, state: FSMContext, userId: int, timeStr: str, isCallback: bool) -> None:
    runAt = parseScheduleTime(timeStr)
    if not runAt:
        text = f"{b('Invalid time')}\n\nUse {c('22:30')} for IST time or {c('+1h')} / {c('+30m')} for relative.\nMin delay: 1 minute."
        if isCallback:
            await msgOrCb.edit_text(text, parse_mode=PM)
        else:
            await msgOrCb.answer(text, parse_mode=PM)
        return

    if runAt < time.time() + 60:
        text = f"{b('Too soon')}\n\nSchedule must be at least 1 minute in the future."
        if isCallback:
            await msgOrCb.edit_text(text, parse_mode=PM)
        else:
            await msgOrCb.answer(text, parse_mode=PM)
        return

    data     = await state.get_data()
    phone    = data["schedPhone"]
    duration = data["schedDuration"]
    workers  = data["schedWorkers"]

    db.addScheduledTest(userId, phone, duration, workers, runAt)
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.button(text="My Schedules", callback_data="menu:schedule")
    builder.button(text="Main Menu",    callback_data="nav:main_menu")
    builder.adjust(1)

    text = (
        f"{b('Test Scheduled')}\n\n"
        f"Phone      {c(phone)}\n"
        f"Duration   {c(formatDuration(duration))}\n"
        f"Workers    {c(str(workers))}\n"
        f"Runs at    {c(formatRunAt(runAt))}\n\n"
        f"{i('You will receive a summary when it finishes.')}"
    )
    if isCallback:
        await msgOrCb.edit_text(text, reply_markup=builder.as_markup(), parse_mode=PM)
    else:
        await msgOrCb.answer(text, reply_markup=builder.as_markup(), parse_mode=PM)