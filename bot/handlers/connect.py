import json
import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.redis import redis_client

router = Router()


@router.message(Command("connect"))
async def cmd_connect(message: Message) -> None:
    telegram_id = message.from_user.id

    # Generate a random 6-digit code
    code = str(random.randint(100000, 999999))

    # Save in Redis with TTL 10 minutes (600 seconds)
    redis_key = f"telegram_connect:{code}"
    payload = json.dumps({"telegram_id": telegram_id})

    await redis_client.set(redis_key, payload, ex=600)

    text = (
        f"Ваш код для прив'язки: <b>{code}</b>\n\n"
        "Введіть його у своєму профілі на сайті. Код дійсний 10 хвилин."
    )
    await message.answer(text, parse_mode="HTML")
