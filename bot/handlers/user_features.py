from __future__ import annotations

import json
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.database import db, IST
from bot.config import ADMIN_ID, PROTECTED_NUMBER
from bot.utils import PM, b, i, c, hEsc

router = Router()

PROTECTED_RESPONSES = [
    "Poda kunne onn!!!",
    "Onn poyeda vadhoori",
    "Ninta pari!",
    "Ntelekk ondaakaan varalletta myre, chethi kallayum panni ninta suna!!",
]


class UserFeatureStates(StatesGroup):
    favoriteLabel  = State()
    favoritePhone  = State()
    presetName     = State()
    referralInput  = State()


# ---------------------------------------------------------------------------
# My Stats
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:stats")
async def cbMyStats(callback: CallbackQuery) -> None:
    userId = callback.from_user.id
    u      = db.getUser(userId)
    if not u:
        await callback.answer()
        return

    totalReqs  = u.get("totalReqs", 0)
    totalOtps  = u.get("totalOtpHits", 0)
    streak     = u.get("streakDays", 0)
    total      = u.get("testsTotal", 0)
    refCount   = db.getReferralCount(userId)
    bonusTests = u.get("bonusTests", 0)
    successRate = f"{round(totalOtps / totalReqs * 100, 1)}%" if totalReqs > 0 else "N/A"

    # Best API from history
    history = db.getUserHistory(userId, limit=20)
    apiTotals: dict = {}
    for h in history:
        snap = h.get("apiSnapshot")
        if not snap:
            continue
        try:
            data = json.loads(snap)
            for name, s in data.items():
                if name not in apiTotals:
                    apiTotals[name] = 0
                apiTotals[name] += s.get("confirmed", 0)
        except Exception:
            pass
    bestApi = max(apiTotals, key=apiTotals.get) if apiTotals else "N/A"

    builder = InlineKeyboardBuilder()
    builder.button(text="Referral Info", callback_data="menu:referral")
    builder.button(text="Main Menu",     callback_data="nav:main_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        f"{b('My Stats')}\n\n"
        f"Tests run     {c(str(total))}\n"
        f"OTPs confirmed {c(str(totalOtps))}\n"
        f"Total requests {c(str(totalReqs))}\n"
        f"Success rate  {c(successRate)}\n"
        f"Best API      {c(hEsc(bestApi))}\n\n"
        f"Streak        {c(str(streak))} days\n"
        f"Referrals     {c(str(refCount))}\n"
        f"Bonus tests   {c(str(bonusTests))}",
        reply_markup=builder.as_markup(),
        parse_mode=PM
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# History with per-test API breakdown
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:history")
async def cbUserHistory(callback: CallbackQuery) -> None:
    userId  = callback.from_user.id
    history = db.getUserHistory(userId, limit=10)
    if not history:
        builder = InlineKeyboardBuilder()
        builder.button(text="Main Menu", callback_data="nav:main_menu")
        await callback.message.edit_text(
            f"{b('My History')}\n\n{i('No tests run yet.')}",
            reply_markup=builder.as_markup(), parse_mode=PM
        )
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    lines   = [f"{b('My History')}  {c(f'last {len(history)}')}\n"]
    for h in history:
        dt = datetime.fromtimestamp(h["startedAt"], tz=IST).strftime("%d %b %H:%M")
        lines.append(
            f"{c(dt)}  {h['phone']}  {h['duration']}s  "
            f"OTP {h['otpHits']}  REQ {h['totalReqs']}"
        )
        builder.button(
            text=f"{h['phone']}  {h['duration']}s  OTP {h['otpHits']}",
            callback_data=f"hist:detail:{h['id']}"
        )
    builder.button(text="Main Menu", callback_data="nav:main_menu")
    builder.adjust(1)
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hist:detail:"))
async def cbHistDetail(callback: CallbackQuery) -> None:
    recordId = int(callback.data.split(":")[2])
    h = db.getTestRecord(recordId)
    if not h or h["userId"] != callback.from_user.id:
        await callback.answer("Not found.", show_alert=True)
        return

    dt      = datetime.fromtimestamp(h["startedAt"], tz=IST).strftime("%d %b %Y %H:%M")
    lines   = [
        f"{b('Test Detail')}\n",
        f"Phone      {c(h['phone'])}",
        f"Date       {c(dt)}",
        f"Duration   {c(str(h['duration']) + 's')}",
        f"Workers    {c(str(h['workers']))}",
        f"Requests   {c(str(h['totalReqs']))}",
        f"OTPs       {c(str(h['otpHits']))}",
        f"Errors     {c(str(h['errors']))}",
        f"Req/sec    {c(str(h['rps']))}",
    ]

    snap = h.get("apiSnapshot")
    if snap:
        try:
            data     = json.loads(snap)
            sorted_  = sorted(data.items(), key=lambda x: x[1].get("confirmed", 0), reverse=True)
            top      = [(n, s) for n, s in sorted_ if s.get("requests", 0) > 0][:6]
            if top:
                lines.append(f"\n{b('API Breakdown')}")
                for name, s in top:
                    lines.append(
                        f"<code>{hEsc(name[:16]):<16}</code>  "
                        f"{c(str(s.get('confirmed', 0)))} otp  "
                        f"{s.get('requests', 0)} req"
                    )
        except Exception:
            pass

    builder = InlineKeyboardBuilder()
    builder.button(text="Back", callback_data="menu:history")
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Favorite numbers
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:favorites")
async def cbFavorites(callback: CallbackQuery) -> None:
    userId = callback.from_user.id
    favs   = db.getFavorites(userId)
    builder = InlineKeyboardBuilder()

    if favs:
        for f in favs:
            label = f["label"] or f["phone"]
            builder.button(text=f"Test: {label}", callback_data=f"fav:test:{f['phone']}")
            builder.button(text="Remove",         callback_data=f"fav:remove:{f['phone']}")
        builder.adjust(2)

    if len(favs) < 3:
        builder.button(text="Add Favorite", callback_data="fav:add")
    builder.button(text="Main Menu", callback_data="nav:main_menu")
    builder.adjust(*(([2] * len(favs)) + [1, 1]))

    text = f"{b('Favorite Numbers')}\n\n"
    if favs:
        for f in favs:
            text += f"{c(f['phone'])}"
            if f["label"]:
                text += f"  {i(hEsc(f['label']))}"
            text += "\n"
    else:
        text += i("No favorites saved yet. Add up to 3 numbers.")

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=PM)
    await callback.answer()


@router.callback_query(F.data == "fav:add")
async def cbFavAdd(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UserFeatureStates.favoritePhone)
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="menu:favorites")
    await callback.message.edit_text(
        f"{b('Add Favorite')}\n\nEnter the 10-digit number to save.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.message(StateFilter(UserFeatureStates.favoritePhone))
async def handleFavPhone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if not phone.isdigit() or len(phone) != 10:
        await message.answer("Enter exactly 10 digits.")
        return
    if phone == PROTECTED_NUMBER and message.from_user.id != ADMIN_ID:
        import random
        await message.answer(random.choice(PROTECTED_RESPONSES))
        return
    await state.update_data(favPhone=phone)
    await state.set_state(UserFeatureStates.favoriteLabel)
    builder = InlineKeyboardBuilder()
    builder.button(text="Skip label", callback_data="fav:nolabel")
    await message.answer(
        f"Number: {c(phone)}\n\nEnter a label (e.g. Home, Work) or skip.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )


@router.callback_query(F.data == "fav:nolabel", StateFilter(UserFeatureStates.favoriteLabel))
async def cbFavNoLabel(callback: CallbackQuery, state: FSMContext) -> None:
    data  = await state.get_data()
    phone = data.get("favPhone", "")
    ok    = db.addFavorite(callback.from_user.id, phone, "")
    await state.clear()
    if ok:
        await callback.answer("Saved.")
    else:
        await callback.answer("Could not save. Already saved or limit reached.", show_alert=True)
    callback.data = "menu:favorites"
    await cbFavorites(callback)


@router.message(StateFilter(UserFeatureStates.favoriteLabel))
async def handleFavLabel(message: Message, state: FSMContext) -> None:
    label = (message.text or "").strip()[:32]
    data  = await state.get_data()
    phone = data.get("favPhone", "")
    ok    = db.addFavorite(message.from_user.id, phone, label)
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="My Favorites", callback_data="menu:favorites")
    builder.button(text="Main Menu",    callback_data="nav:main_menu")
    builder.adjust(1)
    if ok:
        await message.answer(
            f"Saved {c(phone)} as {i(hEsc(label))}." if label else f"Saved {c(phone)}.",
            reply_markup=builder.as_markup(), parse_mode=PM
        )
    else:
        await message.answer(
            "Could not save. You may already have 3 favorites or the number is already saved.",
            reply_markup=builder.as_markup(), parse_mode=PM
        )


@router.callback_query(F.data.startswith("fav:remove:"))
async def cbFavRemove(callback: CallbackQuery) -> None:
    phone = callback.data.split(":", 2)[2]
    db.removeFavorite(callback.from_user.id, phone)
    await callback.answer(f"Removed {phone}.")
    callback.data = "menu:favorites"
    await cbFavorites(callback)


@router.callback_query(F.data.startswith("fav:test:"))
async def cbFavTest(callback: CallbackQuery, state: FSMContext) -> None:
    from bot.handlers.test_flow import TestWizard
    from bot.keyboards.menus import durationKeyboard
    phone  = callback.data.split(":", 2)[2]
    userId = callback.from_user.id

    if db.isPhoneBlacklisted(phone) and userId != ADMIN_ID:
        await callback.answer("That number is blacklisted.", show_alert=True)
        return
    allowed, testsToday, dailyLimit = db.canRunTest(userId)
    if not allowed:
        await callback.answer(f"Daily limit reached. {testsToday}/{dailyLimit} used.", show_alert=True)
        return

    await state.clear()
    await state.update_data(phone=phone)
    await state.set_state(TestWizard.duration)
    await callback.message.edit_text(
        f"{b('Step 1 of 2')}  {c(phone)}\n\nSelect test duration.",
        reply_markup=durationKeyboard(), parse_mode=PM
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Test presets
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:presets")
async def cbPresets(callback: CallbackQuery) -> None:
    userId  = callback.from_user.id
    presets = db.getPresets(userId)
    builder = InlineKeyboardBuilder()

    if presets:
        for p in presets:
            from bot.handlers.test_flow import formatDuration
            label = f"{hEsc(p['name'])}  {p['phone']}  {formatDuration(p['duration'])}"
            builder.button(text=label,    callback_data=f"preset:run:{p['id']}")
            builder.button(text="Delete", callback_data=f"preset:del:{p['id']}")
        builder.adjust(*(([2] * len(presets)) + [1, 1]))
    else:
        builder.adjust(1)

    if len(presets) < 5:
        builder.button(text="Save current as preset", callback_data="preset:save")
    builder.button(text="Main Menu", callback_data="nav:main_menu")

    text = f"{b('Test Presets')}\n\n"
    if presets:
        text += i("Tap a preset to launch it instantly.")
    else:
        text += i("No presets saved. Run a test first, then save it as a preset.")

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=PM)
    await callback.answer()


@router.callback_query(F.data == "preset:save")
async def cbPresetSave(callback: CallbackQuery, state: FSMContext) -> None:
    from bot.handlers.test_flow import _lastConfig
    userId = callback.from_user.id
    last   = _lastConfig.get(userId)
    if not last:
        await callback.answer("No recent test to save. Run a test first.", show_alert=True)
        return
    await state.set_state(UserFeatureStates.presetName)
    await state.update_data(presetData=last)
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="menu:presets")
    from bot.handlers.test_flow import formatDuration
    await callback.message.edit_text(
        f"{b('Save Preset')}\n\n"
        f"Phone    {c(last['phone'])}\n"
        f"Duration {c(formatDuration(last['duration']))}\n"
        f"Workers  {c(str(last['workers']))}\n\n"
        f"Enter a name for this preset.",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


@router.message(StateFilter(UserFeatureStates.presetName))
async def handlePresetName(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()[:32]
    if not name:
        await message.answer("Name cannot be empty.")
        return
    data   = await state.get_data()
    last   = data.get("presetData", {})
    userId = message.from_user.id
    ok = db.addPreset(
        userId=userId,
        name=name,
        phone=last.get("phone", ""),
        duration=last.get("duration", 60),
        workers=last.get("workers", 4),
    )
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="My Presets", callback_data="menu:presets")
    builder.button(text="Main Menu",  callback_data="nav:main_menu")
    builder.adjust(1)
    if ok:
        await message.answer(
            f"Preset {c(hEsc(name))} saved.",
            reply_markup=builder.as_markup(), parse_mode=PM
        )
    else:
        await message.answer(
            "Could not save. You may have 5 presets already or the name is taken.",
            reply_markup=builder.as_markup(), parse_mode=PM
        )


@router.callback_query(F.data.startswith("preset:run:"))
async def cbPresetRun(callback: CallbackQuery, state: FSMContext) -> None:
    from bot.handlers.test_flow import TestWizard, activeRunners
    from bot.keyboards.menus import confirmKeyboard
    from bot.handlers.test_flow import buildConfirmText
    presetId = int(callback.data.split(":")[2])
    preset   = db.getPreset(presetId)
    userId   = callback.from_user.id
    if not preset or preset["userId"] != userId:
        await callback.answer("Preset not found.", show_alert=True)
        return
    if userId in activeRunners:
        await callback.answer("A test is already running.", show_alert=True)
        return
    allowed, testsToday, dailyLimit = db.canRunTest(userId)
    if not allowed:
        await callback.answer(f"Daily limit reached. {testsToday}/{dailyLimit} used.", show_alert=True)
        return
    if db.isPhoneBlacklisted(preset["phone"]) and userId != ADMIN_ID:
        await callback.answer("That number is blacklisted.", show_alert=True)
        return

    await state.set_state(TestWizard.confirm)
    await state.update_data(
        phone=preset["phone"],
        duration=preset["duration"],
        workers=preset["workers"],
        useProxy=False,
        workingProxies=[],
    )
    data = await state.get_data()
    await callback.message.edit_text(
        buildConfirmText(data),
        reply_markup=confirmKeyboard(), parse_mode=PM
    )
    await callback.answer()


@router.callback_query(F.data.startswith("preset:del:"))
async def cbPresetDelete(callback: CallbackQuery) -> None:
    presetId = int(callback.data.split(":")[2])
    db.deletePreset(callback.from_user.id, presetId)
    await callback.answer("Preset deleted.")
    callback.data = "menu:presets"
    await cbPresets(callback)


# ---------------------------------------------------------------------------
# Referral system
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:referral")
async def cbReferral(callback: CallbackQuery) -> None:
    userId   = callback.from_user.id
    code     = db.getReferralCode(userId)
    count    = db.getReferralCount(userId)
    u        = db.getUser(userId)
    bonus    = u.get("bonusTests", 0) if u else 0
    botUsername = (await callback.bot.get_me()).username
    link     = f"https://t.me/{botUsername}?start={code}"

    builder = InlineKeyboardBuilder()
    builder.button(text="Main Menu", callback_data="nav:main_menu")
    await callback.message.edit_text(
        f"{b('Referral Program')}\n\n"
        f"Share your link and earn bonus tests.\n\n"
        f"Your link:\n{c(hEsc(link))}\n\n"
        f"Referrals   {c(str(count))}\n"
        f"Bonus tests {c(str(bonus))}\n\n"
        f"{i('You get +3 tests per referral. They get +1.')}",
        reply_markup=builder.as_markup(), parse_mode=PM
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Handle /start with referral code
# ---------------------------------------------------------------------------

async def handleReferralStart(userId: int, code: str, bot) -> None:
    """Called from start.py when /start has a referral payload."""
    if not code.startswith("ref_"):
        return
    try:
        referrerId = int(code[4:])
    except ValueError:
        return
    applied = db.applyReferral(referrerId, userId)
    if applied:
        try:
            u = db.getUser(referrerId)
            name = u["firstName"] if u else "Someone"
            await bot.send_message(
                referrerId,
                f"New referral! {c(str(db.getReferralCount(referrerId)))} total. You earned +3 bonus tests.",
                parse_mode=PM
            )
        except Exception:
            pass