# Add this function to bot/utils.py
# Then replace all bare `await callback.answer()` calls with `await safeAnswer(callback)`
# and `await callback.answer("text", show_alert=True)` with `await safeAnswer(callback, "text", True)`

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery


async def safeAnswer(callback: CallbackQuery, text: str = "", show_alert: bool = False) -> None:
    """Answer a callback query, silently ignoring stale query errors."""
    try:
        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            pass  # expired — ignore
        else:
            raise
    except Exception:
        pass