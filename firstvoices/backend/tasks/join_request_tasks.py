from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from backend.models import JoinRequest
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE


@shared_task(bind=True)
def delete_old_join_requests(self):
    """
    Deletes join requests that are older than 30 days.
    """
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE)

    thirty_days_ago = timezone.now() - timedelta(days=30)

    try:
        old_join_requests = JoinRequest.objects.filter(created__lte=thirty_days_ago)

        if old_join_requests.exists():
            logger.info(f"Deleting {old_join_requests.count()} old join requests.")

            for join_request in old_join_requests:
                join_request.delete()
        else:
            logger.info(
                "No eligible join requests found for deletion. No action taken."
            )

        logger.info(ASYNC_TASK_END_TEMPLATE)
    except Exception as e:
        self.state = "FAILURE"
        logger.error(f"Error deleting old join requests: {e}")
        logger.info(ASYNC_TASK_END_TEMPLATE)
        raise e
