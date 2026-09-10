import pytest
from django.core.management import call_command
from django_celery_beat.models import CrontabSchedule, PeriodicTask


@pytest.mark.django_db
class TestSetupPeriodicTasks:
    def test_command_creates_tasks_and_is_idempotent(self):
        # Ensure no tasks exist initially
        PeriodicTask.objects.filter(
            name__in=["check_sites_for_mtd_sync", "delete_old_exports"]
        ).delete()
        CrontabSchedule.objects.all().delete()

        # First run should create tasks
        call_command("setup_periodic_tasks")
        assert PeriodicTask.objects.filter(name="check_sites_for_mtd_sync").exists()
        assert PeriodicTask.objects.filter(name="delete_old_exports").exists()

        # Additional runs should not create duplicates
        call_command("setup_periodic_tasks")
        assert PeriodicTask.objects.filter(name="check_sites_for_mtd_sync").count() == 1
        assert PeriodicTask.objects.filter(name="delete_old_exports").count() == 1
