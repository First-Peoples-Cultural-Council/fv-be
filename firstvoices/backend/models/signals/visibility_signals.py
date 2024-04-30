from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.models.jobs import BulkVisibilityJob, JobStatus
from backend.tasks.visibility_tasks import bulk_visibility_change_job
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=BulkVisibilityJob)
def request_bulk_visibility_change(sender, instance, **kwargs):
    """
    Starts the bulk visibility change job when a BulkVisibilityJob is created.
    """
    print("request_bulk_visibility_change")
    if instance.status != JobStatus.ACCEPTED:
        return
    transaction.on_commit(
        lambda: bulk_visibility_change_job.apply_async(
            (instance.id,), link_error=link_error_handler.s()
        )
    )
