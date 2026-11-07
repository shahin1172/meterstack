import logging
from celery import shared_task
from datetime import date, timedelta
from usage.models import UsageRecord

logger = logging.getLogger(__name__)

@shared_task
def cleanup_old_usage():
    """
    Runs every Sunday at 3:00 AM.
    Deletes usage records older than 90 days.
    """
    cutoff = date.today() - timedelta(days=90)
    deleted_count, _ = UsageRecord.objects.filter(timestamp__date__lt=cutoff).delete()

    logger.info("Cleaned up %s old usage records", deleted_count)
    return f"Deleted {deleted_count} records"


@shared_task
def debug_task(message: str) -> str:
    """
    Trivial task used to verify Celery wiring works.
    Logs the message and returns it prefixed with 'processed:'.
    """
    logger.info("debug_task received with arg %r", message)
    return f"processed: {message}"