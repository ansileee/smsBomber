from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.services.database import db
from bot.config import ADMIN_ID

PROTECTED_RESPONSES = [
    "Poda kunne onn!!!",
    "Onn poyeda vadhoori",
    "Ninta pari!",
]


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        # Get user info from event
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user is None:
            return await handler(event, data)

        userId = user.id

        # Register/update user silently
        try:
            db.registerUser(
                userId,
                user.username,
                user.first_name or "User",
                user.last_name,
            )
        except Exception:
            pass

        # Check maintenance mode — let admin through always
        if userId != ADMIN_ID:
            try:
                if db.isMaintenanceMode():
                    msg = db.getMaintenanceMessage()
                    if isinstance(event, Message):
                        await event.answer(f"🔧 {msg}")
                    elif isinstance(event, CallbackQuery):
                        try:
                            await event.answer(f"🔧 {msg}", show_alert=True)
                        except TelegramBadRequest:
                            pass
                    return
            except Exception:
                pass

        # Check ban
        if userId != ADMIN_ID:
            try:
                u = db.getUser(userId)
                if u and u.get("isBanned"):
                    if isinstance(event, Message):
                        await event.answer("Your account has been restricted.")
                    elif isinstance(event, CallbackQuery):
                        try:
                            await event.answer("Your account has been restricted.", show_alert=True)
                        except TelegramBadRequest:
                            pass
                    return
            except Exception:
                pass

        # Run handler — catch stale callback errors globally
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            err = str(e).lower()
            # Suppress known harmless errors
            if any(x in err for x in [
                "query is too old",
                "query id is invalid",
                "message is not modified",
                "message to edit not found",
                "message can't be edited",
            ]):
                return  # silently ignore
            raise  # re-raise anything else
        except Exception:
            raise