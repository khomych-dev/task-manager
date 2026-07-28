from datetime import datetime, timedelta, timezone
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.task import Task
from app.models.user import User
from bot.keyboards import get_task_keyboard

router = Router()


async def get_user_by_telegram_id(session, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalars().first()


@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ваш акаунт не прив'язано. Використайте /connect.")
            return

        stmt = (
            select(Task)
            .where(Task.assignee_id == user.id, Task.status != "done")
            .order_by(Task.deadline.asc().nulls_last())
            .limit(10)
        )
        result = await session.execute(stmt)
        tasks = result.scalars().all()

    if not tasks:
        await message.answer("У вас немає активних задач.")
        return

    await message.answer("Ваші активні задачі (до 10 шт.):")
    for task in tasks:
        task_url = (
            f"{settings.frontend_url}/workspaces/{task.workspace_id}/tasks/{task.id}"
        )
        text = f"<b>{task.title}</b>\nПріоритет: {task.priority}"
        if task.deadline:
            text += f"\nДедлайн: {task.deadline.strftime('%Y-%m-%d %H:%M')}"

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_task_keyboard(str(task.id), task_url),
        )


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ваш акаунт не прив'язано. Використайте /connect.")
            return

        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        stmt = (
            select(Task)
            .where(
                Task.assignee_id == user.id,
                Task.status != "done",
                Task.deadline >= start_of_day,
                Task.deadline < end_of_day,
            )
            .order_by(Task.deadline.asc())
        )
        result = await session.execute(stmt)
        tasks = result.scalars().all()

    if not tasks:
        await message.answer("На сьогодні немає задач.")
        return

    await message.answer("Ваші задачі на сьогодні:")
    for task in tasks:
        task_url = (
            f"{settings.frontend_url}/workspaces/{task.workspace_id}/tasks/{task.id}"
        )
        text = f"<b>{task.title}</b>\nДедлайн: {task.deadline.strftime('%H:%M')}"

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_task_keyboard(str(task.id), task_url),
        )


@router.callback_query(F.data.startswith("done:"))
async def process_task_done(callback: CallbackQuery) -> None:
    task_id_str = callback.data.split(":")[1]
    try:
        task_id = UUID(task_id_str)
    except ValueError:
        await callback.answer("Недійсний ID задачі.", show_alert=True)
        return

    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.answer("Акаунт не прив'язано.", show_alert=True)
            return

        stmt = select(Task).where(Task.id == task_id)
        result = await session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await callback.answer("Задачу не знайдено.", show_alert=True)
            return

        if task.assignee_id != user.id:
            await callback.answer("Це не ваша задача.", show_alert=True)
            return

        task.status = "done"
        await session.commit()

    # Updates the message in Telegram (removes buttons and adds text)
    original_text = (
        callback.message.html_text
        if callback.message.html_text
        else callback.message.text
    )
    await callback.message.edit_text(
        f"✅ {original_text}\n\n<i>Відмічено як виконано</i>",
        reply_markup=None,
        parse_mode="HTML",
    )
    await callback.answer("Задачу виконано!")
