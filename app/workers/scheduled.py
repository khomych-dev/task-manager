import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from celery.schedules import crontab
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.database import async_session_maker
from app.core.redis import redis_client
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Invitation
from app.workers.celery_app import celery_app
from app.workers.tasks import send_email_task, send_telegram_msg_task

logger = structlog.get_logger()


@celery_app.on_after_configure.connect  # type: ignore  # pyright: ignore
def setup_periodic_tasks(sender: Any, **kwargs: Any) -> None:
    # Every 5 minutes — check the tasks with a deadline in 1 hour
    sender.add_periodic_task(
        crontab(minute="*/5"),
        check_deadlines_task.s(),
        name="check_upcoming_deadlines_every_5_mins",
    )

    # Every day at 08:50 UTC — daily digest
    sender.add_periodic_task(
        crontab(hour=8, minute=50),
        send_daily_digest_task.s(),
        name="send_daily_digest_at_0850",
    )

    # Every 24 hours (at midnight) — clear expired invitations
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        clean_expired_invitations_task.s(),
        name="clean_expired_invitations_daily",
    )


async def _check_deadlines_async() -> None:
    now = datetime.now(timezone.utc)
    one_hour_later = now + timedelta(hours=1)

    async with async_session_maker() as session:
        stmt = (
            select(Task, User)
            .join(User, Task.assignee_id == User.id)
            .where(
                Task.deadline > now,
                Task.deadline <= one_hour_later,
                Task.status != "done",
            )
        )
        result = await session.execute(stmt)
        tasks_users = result.all()

        for task, user in tasks_users:
            redis_key = f"deadline_notified:{task.id}"
            is_notified = await redis_client.get(redis_key)

            if not is_notified:
                subject = f"Нагадування: дедлайн задачі '{task.title}' через годину!"
                task_url = f"{settings.frontend_url}/workspaces/{task.workspace_id}/tasks/{task.id}"

                deadline_str = (
                    task.deadline.strftime("%Y-%m-%d %H:%M")
                    if task.deadline
                    else "Unknown"
                )
                body = f"Задача <b>{task.title}</b> має бути виконана до {deadline_str}.<br><a href='{task_url}'>Переглянути</a>"

                send_email_task.delay(user.email, subject, body)
                if user.telegram_id:
                    send_telegram_msg_task.delay(user.telegram_id, subject)

                # Set a key in Redis with a TTL of 2 hours (7,200 seconds)
                await redis_client.set(redis_key, "1", ex=7200)


@celery_app.task(name="check_deadlines_task")  # type: ignore[untyped-decorator]
def check_deadlines_task() -> None:
    logger.info("running_scheduled_task", task="check_deadlines")
    asyncio.run(_check_deadlines_async())


async def _send_daily_digest_async() -> None:
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    async with async_session_maker() as session:
        stmt = (
            select(Task, User)
            .join(User, Task.assignee_id == User.id)
            .where(
                Task.deadline >= start_of_day,
                Task.deadline < end_of_day,
                Task.status != "done",
            )
        )
        result = await session.execute(stmt)
        tasks_users = result.all()

        user_tasks = defaultdict(list)
        user_objects = {}
        for task, user in tasks_users:
            user_tasks[user.id].append(task)
            user_objects[user.id] = user

        for user_id, tasks in user_tasks.items():
            user = user_objects[user_id]
            subject = f"Ваш щоденний дайджест: {len(tasks)} задач на сьогодні"

            body_lines = ["<b>Задачі на сьогодні:</b><ul>"]
            for t in tasks:
                task_url = (
                    f"{settings.frontend_url}/workspaces/{t.workspace_id}/tasks/{t.id}"
                )
                deadline_str = t.deadline.strftime("%H:%M") if t.deadline else "Unknown"
                body_lines.append(
                    f"<li><a href='{task_url}'>{t.title}</a> (до {deadline_str})</li>"
                )
            body_lines.append("</ul>")
            body = "".join(body_lines)

            send_email_task.delay(user.email, subject, body)
            if user.telegram_id:
                send_telegram_msg_task.delay(user.telegram_id, subject)


@celery_app.task(name="send_daily_digest_task")  # type: ignore[untyped-decorator]
def send_daily_digest_task() -> None:
    logger.info("running_scheduled_task", task="send_daily_digest")
    asyncio.run(_send_daily_digest_async())


async def _clean_expired_invitations_async() -> None:
    now = datetime.now(timezone.utc)
    async with async_session_maker() as session:
        stmt = delete(Invitation).where(Invitation.expires_at < now)
        result = await session.execute(stmt)
        await session.commit()
        logger.info("cleaned_expired_invitations", count=getattr(result, "rowcount", 0))


@celery_app.task(name="clean_expired_invitations_task")  # type: ignore[untyped-decorator]
def clean_expired_invitations_task() -> None:
    logger.info("running_scheduled_task", task="clean_expired_invitations")
    asyncio.run(_clean_expired_invitations_async())
