import asyncio

import structlog
from aiogram import Bot, Dispatcher

from app.core.config import settings

logger = structlog.get_logger()


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    await logger.ainfo("Starting Telegram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
