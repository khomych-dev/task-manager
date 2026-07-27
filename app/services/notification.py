import re

from app.core.config import settings
from app.models.task import Task
from app.models.user import User
from app.workers.tasks import send_email_task, send_telegram_msg_task


class NotificationService:
    @staticmethod
    def notify_assignment(task: Task, assignee: User) -> None:
        """Sending a notification about the assignment of a task."""
        subject = f"Вам призначена задача: {task.title}"
        task_url = (
            f"{settings.frontend_url}/workspaces/{task.workspace_id}/tasks/{task.id}"
        )
        body = f"Ви були призначені виконавцем задачі <b>{task.title}</b>.<br><a href='{task_url}'>Переглянути задачу</a>"

        send_email_task.delay(assignee.email, subject, body)
        if assignee.telegram_id:
            send_telegram_msg_task.delay(assignee.telegram_id, subject)

    @staticmethod
    def notify_mention(task: Task, comment_text: str, mentioned_user: User) -> None:
        """Sending a notification about a mention in a comment."""
        subject = f"Вас згадали в коментарі до задачі: {task.title}"
        task_url = (
            f"{settings.frontend_url}/workspaces/{task.workspace_id}/tasks/{task.id}"
        )
        body = f"Вас згадали в коментарі:<br><i>{comment_text}</i><br><a href='{task_url}'>Переглянути задачу</a>"

        send_email_task.delay(mentioned_user.email, subject, body)
        if mentioned_user.telegram_id:
            send_telegram_msg_task.delay(mentioned_user.telegram_id, subject)

    @staticmethod
    def extract_mentions(text: str) -> list[str]:
        """Finds all email addresses in the text that begin with @ (for example, @test@example.com)."""
        return re.findall(r"@([\w\.-]+@[\w\.-]+)", text)
