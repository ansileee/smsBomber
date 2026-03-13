from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.menus import mainMenuKeyboard, backToMainKeyboard
from bot.services.database import db
from bot.config import ADMIN_ID

router = Router()

MAIN_MENU_TEXT = "Main Menu\n\nSelect an option to continue.\n\n— @drazeforce"

HELP_TEXT = (
    "Help\n\n"
    "Start Test\n"
    "  Configure and launch an OTP flood test against all loaded APIs.\n\n"
    "Configuration\n"
    "  Adjust the default worker count and proxy setting.\n\n"
    "During a running test the dashboard updates in real time.\n"
    "Use Stop Test to terminate early and see the final summary.\n\n"
    "Your daily test limit resets at midnight IST."
)


@router.message(CommandStart())
@router.message(Command("menu"))
async def cmdStart(message: Message, state: FSMContext) -> None:
    """Always clears any stuck FSM state before showing the main menu."""
    await state.clear()
    userId = message.from_user.id
    u = db.getUser(userId)
    if u and u["isBanned"]:
        await message.answer("Your account has been restricted.")
        return
    await message.answer(MAIN_MENU_TEXT, reply_markup=mainMenuKeyboard())


@router.callback_query(F.data == "nav:main_menu")
async def cbMainMenu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=mainMenuKeyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cbHelp(callback: CallbackQuery) -> None:
    userId = callback.from_user.id
    u = db.getUser(userId)
    _, testsToday, dailyLimit = db.canRunTest(userId) if u else (False, 0, 0)
    text = HELP_TEXT
    if u:
        text += f"\n\nYour usage today : {testsToday}/{dailyLimit}"
    await callback.message.edit_text(text, reply_markup=backToMainKeyboard())
    await callback.answer()