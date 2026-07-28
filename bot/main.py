import asyncio

import structlog
from aiogram import Bot, Dispatcher

from app.core.config import settings
from bot.handlers import connect, start, tasks

logger = structlog.get_logger()


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Including routers
    dp.include_router(start.router)
    dp.include_router(connect.router)
    dp.include_router(tasks.router)

    await logger.ainfo("Starting Telegram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
