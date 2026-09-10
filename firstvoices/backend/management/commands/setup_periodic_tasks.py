from django.core.management.base import BaseCommand
from django.db import transaction
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from backend.tasks.export_job_tasks import delete_old_exports
from backend.tasks.mtd_export_tasks import check_sites_for_mtd_sync


class Command(BaseCommand):
    help = "Ensure required periodic tasks are created if they do not exist."

    def handle(self, *args, **options):
        # Create the PeriodicTask and schedule for the tasks if they don't exist
        with transaction.atomic():
            schedule, _ = CrontabSchedule.objects.get_or_create(
                hour=21, minute=0, timezone="America/Vancouver"
            )
            PeriodicTask.objects.get_or_create(
                name="check_sites_for_mtd_sync",
                defaults={"crontab": schedule, "task": check_sites_for_mtd_sync.name},
            )

            schedule2, _ = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=0,
                day_of_week="0",
                day_of_month="*",
                month_of_year="*",
                timezone="America/Vancouver",
            )
            PeriodicTask.objects.get_or_create(
                name="delete_old_exports",
                defaults={"crontab": schedule2, "task": delete_old_exports.name},
            )

        self.stdout.write(self.style.SUCCESS("Periodic tasks added/verified."))
