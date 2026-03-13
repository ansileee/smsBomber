from __future__ import annotations

import random
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update

from bot.services.database import db
from bot.config import ADMIN_ID


PROTECTED_RESPONSES = [
    "Poda kunne onn!!!",
    "Onn poyeda vadhoori",
    "Ninta pari!",
    "Ntelekk ondaakaan varalletta myre, chethi kallayum panni ninta suna!!",
]


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user from the update
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        elif isinstance(event, Update):
            if event.message:
                user = event.message.from_user
            elif event.callback_query:
                user = event.callback_query.from_user

        if not user:
            return await handler(event, data)

        userId = user.id

        # Register user and notify admin if new
        isNew = db.registerUser(
            userId=userId,
            username=user.username,
            firstName=user.first_name,
            lastName=user.last_name,
        )

        if isNew and userId != ADMIN_ID:
            await notifyAdminNewUser(data, user)

        return await handler(event, data)


async def notifyAdminNewUser(data: Dict[str, Any], user: Any) -> None:
    try:
        bot = data.get("bot")
        if not bot:
            return
        username = f"@{user.username}" if user.username else "no username"
        name = f"{user.first_name} {user.last_name or ''}".strip()
        text = (
            "New User\n\n"
            f"Name     : {name}\n"
            f"Username : {username}\n"
            f"ID       : {user.id}\n\n"
            f"<a href='tg://user?id={user.id}'>Open DM</a>"
        )
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except Exception:
        pass
