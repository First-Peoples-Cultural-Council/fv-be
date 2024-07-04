import logging
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firstvoices.settings")

app = Celery("firstvoices")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

log = logging.getLogger("celery")


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@app.task(ignore_result=True)
def link_error_handler(request, exc, traceback):
    log.error(f"Task {request.id} failed\n{exc}")


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Importing after django.setup() to avoid AppRegistryNotReady error
    from django_celery_beat.models import IntervalSchedule, PeriodicTask

    from backend.tasks.build_mtd_export_format_tasks import check_sites_for_mtd_sync

    # print a debug message every 3 minutes
    sender.add_periodic_task(
        crontab(minute="*/3"),
        debug_task.s(),
    )

    # Create the PeriodicTask and schedule for the MTD export task if they don't exist
    if not PeriodicTask.objects.filter(name="check_sites_for_mtd_sync").exists():
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=6, period=IntervalSchedule.HOURS
        )

        PeriodicTask.objects.create(
            interval=schedule,
            name="check_sites_for_mtd_sync",
            task=check_sites_for_mtd_sync.name,
        )
