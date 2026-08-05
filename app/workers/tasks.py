import asyncio

import structlog
from celery import shared_task
from fastapi_mail import MessageSchema, MessageType

from app.core.email import fast_mail

logger = structlog.get_logger()


async def _send_email_async(email_to: str, subject: str, body: str) -> None:
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],  # type: ignore[list-item]
        body=body,
        subtype=MessageType.html,
    )
    try:
        await fast_mail.send_message(message)
        logger.info("email_sent_successfully", email=email_to)
    except Exception as e:
        logger.error("email_send_failed", error=str(e), email=email_to)


@shared_task(name="send_email_task")  # type: ignore[untyped-decorator]
def send_email_task(email_to: str, subject: str, body: str) -> None:
    """A background task for sending emails."""
    asyncio.run(_send_email_async(email_to, subject, body))


@shared_task(name="send_telegram_msg_task")  # type: ignore[untyped-decorator]
def send_telegram_msg_task(telegram_id: int, message: str) -> None:
    """A background task for sending a message on Telegram."""
    logger.info("telegram_message_queued", telegram_id=telegram_id, message=message)
