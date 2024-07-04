from django.apps import AppConfig
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class BackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend"

    def ready(self):
        import backend.models.signals  # noqa F401
        import backend.search.signals  # noqa F401

        # Create the PeriodicTask and schedule for the MTD export task if they don't exist
        if not PeriodicTask.objects.filter(name="sync_mtd_index").exists():
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=6, period=IntervalSchedule.HOURS
            )

            PeriodicTask.objects.create(
                interval=schedule,
                name="sync_mtd_index",
                task="backend.tasks.check_sites_for_mtd_sync",
            )
