import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.handlers import start, test_flow, dashboard, admin
from bot.handlers import admin_apis, admin_proxy
from bot.middleware.auth import AuthMiddleware
from bot.services.scheduler import midnightResetLoop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware - runs on every incoming update
    dp.update.middleware(AuthMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(test_flow.router)
    dp.include_router(dashboard.router)
    dp.include_router(admin.router)
    dp.include_router(admin_apis.router)
    dp.include_router(admin_proxy.router)

    # Background scheduler for midnight IST reset
    asyncio.create_task(midnightResetLoop())

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
