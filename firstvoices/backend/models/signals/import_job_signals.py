from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.models.import_jobs import ImportJob
from backend.tasks.import_job_tasks import execute_dry_run_import
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=ImportJob)
def request_dry_run_import(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(
            lambda: execute_dry_run_import.apply_async(
                (str(instance.id),), link_error=link_error_handler.s()
            )
        )
