from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.models.import_jobs import ImportJob
from backend.tasks.import_job_tasks import execute_dry_run_import


@receiver(post_save, sender=ImportJob)
def request_dry_run_import(sender, instance, **kwargs):
    execute_dry_run_import(instance)
