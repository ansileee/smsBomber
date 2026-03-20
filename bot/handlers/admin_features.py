from __future__ import annotations

import json

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADMIN_ID
from bot.services.database import db
from bot.utils import PM, b, i, c, hEsc

router = Router()


def isAdmin(userId: int) -> bool:
    return userId == ADMIN_ID


class AdminExtraStates(StatesGroup):
    waitingMaintenanceMsg = State()
    waitingUserSearch     = State()


# ---------------------------------------------------------------------------
# Test analytics dashboard
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:analytics")
async def cbAnalytics(callback: CallbackQuery) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    stats  = db.getAnalytics()
    users  = db.getAllUsers(offset=0, limit=9999)
    banned = sum(1 for u in users if u["isBanned"])
    active = sum(1 for u in users if u["testsToday"] > 0)

    topApis = db.getTopApis(limit=5)
    apiLines = []
    for a in topApis:
        rate = f"{round(a['totalOtps'] / a['totalReqs'] * 100, 1)}%" if a["totalReqs"] > 0 else "0%"
        apiLines.append(
            f"<code>{hEsc(a['name'][:16]):<16}</code>  "
            f"{c(str(a['totalOtps']))} otp  {a['totalReqs']} req  {rate}"
        )
    apiBlock = "\n".join(apiLines) if apiLines else i("No data yet.")

    builder = InlineKeyboardBuilder()
    builder.button(text="Full API Stats", callback_data="adm:apistats:0")
    builder.button(text="Leaderboard",    callback_data="adm:leaderboard")
    builder.button(text="Admin Menu",     callback_data="adm:menu")
    builder.adjust(2, 1)

    await callback.message.edit_text(
        f"{b('Analytics')}\n\n"
        f"Today\n"
        f"Tests run   {c(str(stats['todayTests']))}\n"
        f"Requests    {c(str(stats['todayReqs']))}\n\n"
        f"All time\n"
        f"Tests run   {c(str(stats['totalTests']))}\n"
        f"Requests    {c(str(stats['totalReqs']))}\n"
        f"OTPs        {c(str(stats['totalOtps']))}\n\n"
        f"Users\n"
        f"Total       {c(str(len(users)))}\n"
        f"Active today {c(str(active))}\n"
        f"Banned      {c(str(banned))}\n\n"
        f"{b('Top APIs')}\n{apiBlock}",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Full API stats (paginated)
# ---------------------------------------------------------------------------

APISTATS_PER_PAGE = 8

@router.callback_query(F.data.startswith("adm:apistats:"))
async def cbApiStats(callback: CallbackQuery) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    page    = int(callback.data.split(":")[2])
    allApis = db.getAllApiStats()
    if not allApis:
        builder = InlineKeyboardBuilder()
        builder.button(text="Back", callback_data="adm:analytics")
        await callback.message.edit_text(
            f"{b('API Stats')}\n\n{i('No data yet. Run some tests first.')}",
            reply_markup=builder.as_markup(), parse_mode=PM
        )
        await callback.answer()
        return

    total      = len(allApis)
    totalPages = max(1, -(-total // APISTATS_PER_PAGE))
    start      = page * APISTATS_PER_PAGE
    pageApis   = allApis[start:start + APISTATS_PER_PAGE]

    lines = [f"{b('API Stats')}  {c(f'page {page+1}/{totalPages}')}\n"]
    for a in pageApis:
        rate = f"{round(a['totalOtps'] / a['totalReqs'] * 100, 1)}%" if a["totalReqs"] > 0 else "0%"
        lines.append(
            f"<code>{hEsc(a['name'][:16]):<16}</code>  "
            f"{c(str(a['totalOtps']))} otp  {a['totalReqs']} req  {c(rate)}"
        )

    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="Prev", callback_data=f"adm:apistats:{page-1}")
    if page < totalPages - 1:
        builder.button(text="Next", callback_data=f"adm:apistats:{page+1}")
    builder.button(text="Back", callback_data="adm:analytics")
    builder.adjust(2, 1)

    await callback.message.edit_text(
        "\n".join(lines), reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Top users leaderboard
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:leaderboard")
async def cbLeaderboard(callback: CallbackQuery) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    topUsers = db.getTopUsers(limit=10)
    lines    = [f"{b('Top Users')}\n"]
    medals   = ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10."]
    for n, u in enumerate(topUsers):
        name = u["firstName"] or "Unknown"
        un   = f"@{u['username']}" if u.get("username") else str(u["userId"])
        lines.append(
            f"{medals[n]}  {hEsc(name)}  {c(un)}\n"
            f"    {u.get('testsTotal', 0)} tests  {u.get('totalOtpHits', 0)} OTPs"
        )

    builder = InlineKeyboardBuilder()
    builder.button(text="Back", callback_data="adm:analytics")
    await callback.message.edit_text(
        "\n".join(lines) if topUsers else f"{b('Leaderboard')}\n\n{i('No data yet.')}",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Maintenance mode
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:maintenance")
async def cbMaintenance(callback: CallbackQuery) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    enabled = db.isMaintenanceMode()
    msg     = db.getMaintenanceMessage()
    label   = "Disable Maintenance" if enabled else "Enable Maintenance"
    status  = "ON" if enabled else "OFF"

    builder = InlineKeyboardBuilder()
    builder.button(text=label,            callback_data="adm:maintenance_toggle")
    builder.button(text="Set Message",    callback_data="adm:maintenance_msg")
    builder.button(text="Admin Menu",     callback_data="adm:menu")
    builder.adjust(2, 1)

    await callback.message.edit_text(
        f"{b('Maintenance Mode')}\n\n"
        f"Status   {c(status)}\n\n"
        f"Message:\n{i(hEsc(msg))}",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.callback_query(F.data == "adm:maintenance_toggle")
async def cbMaintenanceToggle(callback: CallbackQuery) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    current = db.isMaintenanceMode()
    db.setMaintenanceMode(not current)
    status = "enabled" if not current else "disabled"
    await callback.answer(f"Maintenance mode {status}.")
    await cbMaintenance(callback)


@router.callback_query(F.data == "adm:maintenance_msg")
async def cbMaintenanceMsg(callback: CallbackQuery, state: FSMContext) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    await state.set_state(AdminExtraStates.waitingMaintenanceMsg)
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="adm:maintenance")
    await callback.message.edit_text(
        f"{b('Set Maintenance Message')}\n\nType the message users will see while maintenance is on.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.message(StateFilter(AdminExtraStates.waitingMaintenanceMsg))
async def handleMaintenanceMsg(message: Message, state: FSMContext) -> None:
    if not isAdmin(message.from_user.id):
        return
    msg = (message.text or "").strip()
    if not msg:
        await message.answer("Message cannot be empty.")
        return
    db.setMaintenanceMessage(msg)
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="Maintenance Settings", callback_data="adm:maintenance")
    await message.answer(
        f"Maintenance message updated.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )


# ---------------------------------------------------------------------------
# User search
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:search")
async def cbSearch(callback: CallbackQuery, state: FSMContext) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    await state.set_state(AdminExtraStates.waitingUserSearch)
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="adm:menu")
    await callback.message.edit_text(
        f"{b('Search Users')}\n\nEnter a username, name, or user ID.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.message(StateFilter(AdminExtraStates.waitingUserSearch))
async def handleUserSearch(message: Message, state: FSMContext) -> None:
    if not isAdmin(message.from_user.id):
        return
    query   = (message.text or "").strip()
    results = db.searchUsers(query)
    await state.clear()
    if not results:
        builder = InlineKeyboardBuilder()
        builder.button(text="Search Again", callback_data="adm:search")
        builder.button(text="Admin Menu",   callback_data="adm:menu")
        builder.adjust(1)
        await message.answer(
            f"No users found for {c(hEsc(query))}.",
            reply_markup=builder.as_markup(), parse_mode=PM
        )
        return
    builder = InlineKeyboardBuilder()
    for u in results[:10]:
        name  = u["firstName"] or "Unknown"
        total = u.get("testsTotal", 0)
        label = f"{name}  -  {total} tests"
        builder.button(text=label, callback_data=f"adm:user:{u['userId']}")
    builder.button(text="Admin Menu", callback_data="adm:menu")
    builder.adjust(1)
    await message.answer(
        f"{b('Search Results')}  {c(str(len(results)) + ' found')}\n\n{i('Tap a user to manage them.')}",
        reply_markup=builder.as_markup(), parse_mode=PM
    )