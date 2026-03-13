from __future__ import annotations

import asyncio
from typing import Dict, Optional

from aiogram import Router, F # type: ignore
from aiogram.filters import StateFilter # type: ignore
from aiogram.fsm.context import FSMContext # type: ignore
from aiogram.fsm.state import State, StatesGroup # type: ignore
from aiogram.types import Message, CallbackQuery # type: ignore

from bot.keyboards.menus import (
    durationKeyboard,
    workersKeyboard,
    proxyKeyboard,
    confirmKeyboard,
    runningKeyboard,
    finishedKeyboard,
    mainMenuKeyboard,
)
from bot.services.tester_runner import TesterRunner, validateProxies
from bot.services.proxy_manager import proxyManager
from bot.services.database import db
from bot.config import DASHBOARD_UPDATE_INTERVAL, ADMIN_ID, PROTECTED_NUMBER

import random

router = Router()

activeRunners: Dict[int, TesterRunner] = {}
dashboardTasks: Dict[int, asyncio.Task] = {}
summaryShown: Dict[int, bool] = {}
activeRecordIds: Dict[int, int] = {}

PROTECTED_RESPONSES = [
    "Poda kunne onn!!!",
    "Onn poyeda vadhoori",
    "Ninta pari!",
    "Ntelekk ondaakaan varalletta myre, chethi kallayum panni ninta suna!!",
]


class TestWizard(StatesGroup):
    phone = State()
    duration = State()
    durationCustom = State()
    workers = State()
    workersCustom = State()
    proxy = State()
    proxyChecking = State()
    confirm = State()
    running = State()


def formatDuration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m = seconds // 60
        s = seconds % 60
        return f"{m}m {s}s" if s else f"{m}m"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m" if m else f"{h}h"


def parseTime(t: str) -> Optional[int]:
    try:
        if t.endswith("s"):
            return int(t[:-1])
        if t.endswith("m"):
            return int(t[:-1]) * 60
        if t.endswith("h"):
            return int(t[:-1]) * 3600
        return int(t)
    except (ValueError, AttributeError):
        return None


def buildConfirmText(data: dict, proxyInfo: str = "") -> str:
    proxyLabel = proxyInfo if proxyInfo else ("Proxy file" if data.get("useProxy") else "None")
    return (
        "Test Configuration\n\n"
        f"Phone    : {data['phone']}\n"
        f"Duration : {formatDuration(data['duration'])}\n"
        f"Workers  : {data['workers']}\n"
        f"Proxy    : {proxyLabel}\n\n"
        "Confirm to launch."
    )


def buildDashboardText(snap: dict, phone: str, duration: int) -> str:
    elapsed = snap["elapsed"]
    remaining = max(0, duration - elapsed)

    lines = []
    for name, s in snap["perApi"].items():
        if s["success"] > 0 or s["fail"] > 0 or s["otp"] > 0:
            lines.append(
                f"{name}  OK {s['success']}  FAIL {s['fail']}  OTP {s['otp']}  {s['avgMs']}ms"
            )

    if not lines:
        apiBlock = "Waiting for responses..."
    else:
        apiBlock = "\n".join(lines[:15])
        if len(lines) > 15:
            apiBlock += f"\n... and {len(lines) - 15} more"

    return (
        "Running Test\n\n"
        f"Target    : {phone}\n"
        f"Elapsed   : {formatDuration(int(elapsed))}   Remaining : {formatDuration(int(remaining))}\n\n"
        f"Requests  : {snap['total']}\n"
        f"OTP sent  : {snap['otpSent']}\n"
        f"Errors    : {snap['errors']}\n"
        f"Req / sec : {snap['rps']}\n\n"
        "Per-API\n"
        f"{apiBlock}"
    )


def buildSummaryText(snap: dict, phone: str) -> str:
    sortedApis = sorted(
        snap["perApi"].items(),
        key=lambda x: (x[1]["otp"], x[1]["success"]),
        reverse=True,
    )
    topLines = []
    for name, s in sortedApis[:5]:
        if s["success"] > 0 or s["otp"] > 0:
            topLines.append(f"{name}  OTP {s['otp']}  OK {s['success']}  FAIL {s['fail']}")

    topBlock = "\n".join(topLines) if topLines else "No successful responses recorded."

    return (
        "Test Results\n\n"
        f"Target    : {phone}\n"
        f"Duration  : {formatDuration(int(snap['elapsed']))}\n\n"
        f"Requests  : {snap['total']}\n"
        f"OTP hits  : {snap['otpSent']}\n"
        f"Errors    : {snap['errors']}\n"
        f"Req / sec : {snap['rps']}\n\n"
        "Top APIs\n"
        f"{topBlock}"
    )


async def dashboardLoop(
    runner: TesterRunner,
    message: Message,
    phone: str,
    duration: int,
    userId: int,
    state: FSMContext,
) -> None:
    lastText = ""
    while runner.isRunning:
        await asyncio.sleep(DASHBOARD_UPDATE_INTERVAL)
        snap = runner.stats.snapshot()
        newText = buildDashboardText(snap, phone, duration)
        if newText != lastText:
            try:
                await message.edit_text(newText, reply_markup=runningKeyboard())
                lastText = newText
            except Exception:
                pass

    if not summaryShown.get(userId, False):
        summaryShown[userId] = True
        snap = runner.stats.snapshot()
        _saveHistory(userId, snap)
        summary = buildSummaryText(snap, phone)
        try:
            await message.edit_text(summary, reply_markup=finishedKeyboard())
        except Exception:
            await message.answer(summary, reply_markup=finishedKeyboard())

    activeRunners.pop(userId, None)
    dashboardTasks.pop(userId, None)
    summaryShown.pop(userId, None)
    activeRecordIds.pop(userId, None)
    await state.clear()


def _saveHistory(userId: int, snap: dict) -> None:
    recordId = activeRecordIds.get(userId)
    if recordId:
        try:
            db.finishTestRecord(
                recordId=recordId,
                totalReqs=snap["total"],
                otpHits=snap["otpSent"],
                errors=snap["errors"],
                rps=snap["rps"],
            )
        except Exception:
            pass


@router.callback_query(F.data == "menu:start_test")
async def cbStartTest(callback: CallbackQuery, state: FSMContext) -> None:
    userId = callback.from_user.id
    if userId in activeRunners:
        await callback.answer("A test is already running. Stop it first.", show_alert=True)
        return

    allowed, testsToday, dailyLimit = db.canRunTest(userId)
    if not allowed:
        u = db.getUser(userId)
        if u and u["isBanned"]:
            await callback.answer("Your account has been restricted.", show_alert=True)
            return
        await callback.answer(
            f"Daily limit reached. You have used {testsToday}/{dailyLimit} tests today.",
            show_alert=True
        )
        try:
            u = db.getUser(userId)
            username = f"@{u['username']}" if u and u.get("username") else str(userId)
            await callback.bot.send_message(
                ADMIN_ID,
                f"Limit hit\n\nUser {username} (ID: {userId}) hit their daily limit of {dailyLimit}."
            )
        except Exception:
            pass
        return

    await state.clear()
    await state.set_state(TestWizard.phone)
    await callback.message.edit_text(
        "Start Test\n\n"
        "Enter the 10-digit mobile number.\n"
        "Example: 9876543210"
    )
    await callback.answer()


@router.message(StateFilter(TestWizard.phone))
async def handlePhone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()

    if not phone.isdigit() or len(phone) != 10:
        await message.answer(
            "Invalid number.\n\n"
            "Enter exactly 10 digits with no spaces or symbols.\n"
            "Example: 9876543210"
        )
        return

    if phone == PROTECTED_NUMBER and message.from_user.id != ADMIN_ID:
        await message.answer(random.choice(PROTECTED_RESPONSES))
        return

    if db.isPhoneBlacklisted(phone) and message.from_user.id != ADMIN_ID:
        await message.answer(
            "That number is not available for testing."
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(TestWizard.duration)
    await message.answer(
        "Test Duration\n\nSelect how long the test should run.",
        reply_markup=durationKeyboard(),
    )


@router.callback_query(F.data.startswith("duration:"), StateFilter(TestWizard.duration))
async def cbDuration(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":")[1]
    if value == "custom":
        await state.set_state(TestWizard.durationCustom)
        await callback.message.edit_text(
            "Custom Duration\n\n"
            "Enter a number with a unit:\n"
            "  30s  /  5m  /  1h\n\n"
            "Minimum: 5s   Maximum: 24h"
        )
        await callback.answer()
        return
    await state.update_data(duration=int(value))
    await state.set_state(TestWizard.workers)
    await callback.message.edit_text(
        "Sender Workers\n\nSelect the number of concurrent workers.",
        reply_markup=workersKeyboard(),
    )
    await callback.answer()


@router.message(StateFilter(TestWizard.durationCustom))
async def handleDurationCustom(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    seconds = parseTime(raw)
    if seconds is None or seconds < 5 or seconds > 86400:
        await message.answer(
            "Invalid duration.\n\n"
            "Examples: 30s  /  5m  /  2h\n"
            "Minimum: 5s   Maximum: 24h"
        )
        return
    await state.update_data(duration=seconds)
    await state.set_state(TestWizard.workers)
    await message.answer(
        "Sender Workers\n\nSelect the number of concurrent workers.",
        reply_markup=workersKeyboard(),
    )


@router.callback_query(F.data == "nav:duration")
async def cbBackToDuration(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TestWizard.duration)
    await callback.message.edit_text(
        "Test Duration\n\nSelect how long the test should run.",
        reply_markup=durationKeyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("workers:"), StateFilter(TestWizard.workers))
async def cbWorkers(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":")[1]
    if value == "custom":
        await state.set_state(TestWizard.workersCustom)
        await callback.message.edit_text(
            "Custom Workers\n\nEnter a number between 1 and 64."
        )
        await callback.answer()
        return
    await state.update_data(workers=int(value))
    await state.set_state(TestWizard.proxy)
    hasProxies = proxyManager.hasProxies()
    await callback.message.edit_text(
        "Proxy Settings\n\nSelect proxy mode for this test.",
        reply_markup=proxyKeyboard(hasProxies),
    )
    await callback.answer()


@router.message(StateFilter(TestWizard.workersCustom))
async def handleWorkersCustom(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    try:
        workers = int(raw)
        if not 1 <= workers <= 64:
            raise ValueError
    except ValueError:
        await message.answer("Enter a whole number between 1 and 64.")
        return
    await state.update_data(workers=workers)
    await state.set_state(TestWizard.proxy)
    hasProxies = proxyManager.hasProxies()
    await message.answer(
        "Proxy Settings\n\nSelect proxy mode for this test.",
        reply_markup=proxyKeyboard(hasProxies),
    )


@router.callback_query(F.data == "nav:workers")
async def cbBackToWorkers(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TestWizard.workers)
    await callback.message.edit_text(
        "Sender Workers\n\nSelect the number of concurrent workers.",
        reply_markup=workersKeyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("proxy:"), StateFilter(TestWizard.proxy))
async def cbProxy(callback: CallbackQuery, state: FSMContext) -> None:
    useProxy = callback.data == "proxy:file"
    await state.update_data(useProxy=useProxy)

    if useProxy:
        await state.set_state(TestWizard.proxyChecking)
        statusMsg = await callback.message.edit_text(
            "Checking Proxies\n\nVerifying proxy list, please wait..."
        )
        await callback.answer()

        allProxies = proxyManager.getAllProxies()
        if not allProxies:
            await state.update_data(useProxy=False, workingProxies=[])
            data = await state.get_data()
            await state.set_state(TestWizard.confirm)
            await statusMsg.edit_text(
                buildConfirmText(data, proxyInfo="None (no proxies loaded)"),
                reply_markup=confirmKeyboard(),
            )
            return

        working = await validateProxies(allProxies)
        dead = len(allProxies) - len(working)
        await state.update_data(workingProxies=working)

        proxyInfo = f"{len(working)} working / {dead} dead"
        if not working:
            await state.update_data(useProxy=False)
            proxyInfo = "None (0 working proxies found)"

        data = await state.get_data()
        await state.set_state(TestWizard.confirm)
        await statusMsg.edit_text(
            buildConfirmText(data, proxyInfo=proxyInfo),
            reply_markup=confirmKeyboard(),
        )
    else:
        await state.set_state(TestWizard.confirm)
        data = await state.get_data()
        await callback.message.edit_text(
            buildConfirmText(data),
            reply_markup=confirmKeyboard(),
        )
        await callback.answer()


@router.callback_query(F.data == "confirm:cancel", StateFilter(TestWizard.confirm))
async def cbCancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Test cancelled.", reply_markup=mainMenuKeyboard())
    await callback.answer()


@router.callback_query(F.data == "confirm:start", StateFilter(TestWizard.confirm))
async def cbConfirmStart(callback: CallbackQuery, state: FSMContext) -> None:
    userId = callback.from_user.id
    if userId in activeRunners:
        await callback.answer("A test is already running.", show_alert=True)
        return

    allowed, testsToday, dailyLimit = db.canRunTest(userId)
    if not allowed:
        await state.clear()
        await callback.message.edit_text(
            f"Daily limit reached. {testsToday}/{dailyLimit} tests used today.\n\n"
            "Your limit resets at midnight IST.",
            reply_markup=mainMenuKeyboard(),
        )
        await callback.answer()
        return

    data = await state.get_data()
    await state.set_state(TestWizard.running)

    phone = data["phone"]
    duration = data["duration"]
    workers = data["workers"]
    useProxy = data.get("useProxy", False)
    workingProxies = data.get("workingProxies", [])

    db.incrementTestCount(userId)
    recordId = db.startTestRecord(userId, phone, duration, workers)
    activeRecordIds[userId] = recordId

    runner = TesterRunner(
        phone=phone,
        duration=duration,
        workers=workers,
        useProxy=useProxy,
        proxyList=workingProxies,
    )
    activeRunners[userId] = runner
    summaryShown[userId] = False

    _, testsNow, dailyLimitNow = db.canRunTest(userId)
    usageNote = f"Tests today : {testsNow}/{dailyLimitNow}"

    dashMsg = await callback.message.edit_text(
        "Running Test\n\n"
        f"Target    : {phone}\n"
        f"Duration  : {formatDuration(duration)}\n"
        f"{usageNote}\n\n"
        "Initializing...",
        reply_markup=runningKeyboard(),
    )
    await callback.answer()

    await runner.start()

    task = asyncio.create_task(
        dashboardLoop(runner, dashMsg, phone, duration, userId, state)
    )
    dashboardTasks[userId] = task


@router.callback_query(F.data == "test:stop")
async def cbStopTest(callback: CallbackQuery, state: FSMContext) -> None:
    userId = callback.from_user.id
    runner = activeRunners.get(userId)
    if not runner:
        await callback.answer("No active test found.", show_alert=True)
        return

    await callback.answer("Stopping...")
    summaryShown[userId] = True

    task = dashboardTasks.pop(userId, None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await runner.stop()

    snap = runner.stats.snapshot()
    _saveHistory(userId, snap)

    activeRunners.pop(userId, None)
    summaryShown.pop(userId, None)
    activeRecordIds.pop(userId, None)
    await state.clear()

    summary = buildSummaryText(snap, runner.phone)
    try:
        await callback.message.edit_text(summary, reply_markup=finishedKeyboard())
    except Exception:
        await callback.message.answer(summary, reply_markup=finishedKeyboard())


@router.callback_query(F.data == "test:refresh")
async def cbRefresh(callback: CallbackQuery) -> None:
    userId = callback.from_user.id
    runner = activeRunners.get(userId)
    if not runner:
        await callback.answer("No active test.", show_alert=True)
        return
    snap = runner.stats.snapshot()
    newText = buildDashboardText(snap, runner.phone, runner.duration)
    try:
        await callback.message.edit_text(newText, reply_markup=runningKeyboard())
    except Exception:
        pass
    await callback.answer("Refreshed.")