from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.menus import mainMenuKeyboard, backToMainKeyboard
from bot.services.database import db
from bot.config import ADMIN_ID
from bot.utils import PM, b, i, c, hEsc

router = Router()


def mainMenuText(userId: int) -> str:
    from bot.services.api_manager import apiManager
    total   = len(apiManager.getMergedConfigs())
    skipped = len(db.getSkippedApiNames())
    active  = total - skipped
    u       = db.getUser(userId)
    if u:
        _, testsToday, dailyLimit = db.canRunTest(userId)
        streak  = u.get("streakDays", 0)
        streakStr = f"  {c(str(streak) + ' day streak')}" if streak > 1 else ""
        status  = f"Tests today: {testsToday}/{dailyLimit}{streakStr}"
        banned  = "  [BANNED]" if u["isBanned"] else ""
    else:
        status = "New user"
        banned = ""
        streakStr = ""
    skip_str = f"  {c(str(skipped))} skipped" if skipped else ""
    return (
        f"{b('smsBomber')}\n\n"
        f"APIs loaded   {c(str(active))} active{skip_str}\n"
        f"{c(status)}{banned}\n\n"
        f"{i('by @drazeforce')}"
    )


HELP_TEXT = (
    "<b>Help</b>\n\n"
    "<b>Start Test</b>\n"
    "Pick a target number, set duration and workers, then launch.\n\n"
    "<b>Favorites</b>\n"
    "Save up to 3 numbers for quick access.\n\n"
    "<b>Presets</b>\n"
    "Save full test configs (phone + duration + workers) and launch in one tap.\n\n"
    "<b>My Stats</b>\n"
    "View your OTP success rate, streak, and best performing API.\n\n"
    "<b>Referral</b>\n"
    "Share your link. You get +3 tests per referral, they get +1.\n\n"
    "<b>Settings</b>\n"
    "Set default workers and proxy preference.\n\n"
    "<b>Dashboard</b>\n"
    "Updates live every 2s. Shows confirmed OTPs, 2xx responses, errors, and per-API breakdown.\n\n"
    "<b>Confirmed OTPs</b> = 2xx response <i>and</i> body contains success keywords.\n"
    "<b>2xx Total</b> = all successful HTTP responses.\n\n"
    "<i>Daily limit resets at midnight IST.</i>"
)


@router.message(CommandStart())
async def cmdStart(message: Message, state: FSMContext) -> None:
    await state.clear()
    userId = message.from_user.id

    # Maintenance mode check (bypass for admin)
    if userId != ADMIN_ID and db.isMaintenanceMode():
        await message.answer(db.getMaintenanceMessage())
        return

    u = db.getUser(userId)
    if u and u["isBanned"]:
        await message.answer("Your account has been restricted.")
        return

    # Handle referral code from deep link e.g. /start ref_12345
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        code = args[1].strip()
        from bot.handlers.user_features import handleReferralStart
        await handleReferralStart(userId, code, message.bot)

    await message.answer(mainMenuText(userId), reply_markup=mainMenuKeyboard(), parse_mode=PM)


@router.message(Command("menu"))
async def cmdMenu(message: Message, state: FSMContext) -> None:
    await state.clear()
    userId = message.from_user.id
    if userId != ADMIN_ID and db.isMaintenanceMode():
        await message.answer(db.getMaintenanceMessage())
        return
    u = db.getUser(userId)
    if u and u["isBanned"]:
        await message.answer("Your account has been restricted.")
        return
    await message.answer(mainMenuText(userId), reply_markup=mainMenuKeyboard(), parse_mode=PM)


@router.callback_query(F.data == "nav:main_menu")
async def cbMainMenu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        mainMenuText(callback.from_user.id),
        reply_markup=mainMenuKeyboard(),
        parse_mode=PM
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cbHelp(callback: CallbackQuery) -> None:
    userId = callback.from_user.id
    u      = db.getUser(userId)
    _, testsToday, dailyLimit = db.canRunTest(userId) if u else (False, 0, 0)
    text = HELP_TEXT
    if u:
        text += f"\n\n{c(f'Your usage: {testsToday}/{dailyLimit} today')}"
    await callback.message.edit_text(text, reply_markup=backToMainKeyboard(), parse_mode=PM)
    await callback.answer()