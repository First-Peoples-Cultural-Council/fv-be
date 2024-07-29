import logging
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firstvoices.settings")

app = Celery("firstvoices")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

log = logging.getLogger("celery")


@app.task(ignore_result=True)
def link_error_handler(request, exc, traceback):
    log.error(f"Task {request.id} failed\n{exc}")


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Importing after django.setup() to avoid AppRegistryNotReady error
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    from backend.tasks.build_mtd_export_format_tasks import check_sites_for_mtd_sync

    # Create the PeriodicTask and schedule for the MTD export task if they don't exist
    if not PeriodicTask.objects.filter(name="check_sites_for_mtd_sync").exists():
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=21, minute=0, timezone="America/Vancouver"
        )

        PeriodicTask.objects.create(
            crontab=schedule,
            name="check_sites_for_mtd_sync",
            task=check_sites_for_mtd_sync.name,
        )
