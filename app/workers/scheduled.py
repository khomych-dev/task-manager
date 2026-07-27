import structlog
from celery.schedules import crontab

from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
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


@celery_app.task(name="check_deadlines_task")
def check_deadlines_task():
    """Checking the assignments with a deadline in 1 hour."""
    logger.info("running_scheduled_task", task="check_deadlines")


@celery_app.task(name="send_daily_digest_task")
def send_daily_digest_task():
    """Compiling and sending a daily digest."""
    logger.info("running_scheduled_task", task="send_daily_digest")


@celery_app.task(name="clean_expired_invitations_task")
def clean_expired_invitations_task():
    """Deleting expired invitations from the database."""
    logger.info("running_scheduled_task", task="clean_expired_invitations")
