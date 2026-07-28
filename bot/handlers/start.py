from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Вітаю! Це Task Manager бот.\n\n"
        "Щоб отримувати нотифікації та керувати задачами, вам потрібно прив'язати свій акаунт.\n\n"
        "Використайте команду /connect, щоб отримати 6-значний код для прив'язки, "
        "а потім введіть його у своєму профілі на сайті."
    )
    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "Доступні команди:\n"
        "/start — Привітання та інструкція\n"
        "/connect — Отримати код для прив'язки акаунту\n"
        "/tasks — Список моїх задач\n"
        "/today — Задачі з дедлайном сьогодні\n"
        "/workspaces — Список моїх workspace\n"
        "/help — Список всіх команд"
    )
    await message.answer(text)
