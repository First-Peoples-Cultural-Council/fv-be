from django.db.models import Q
from rest_framework.exceptions import ValidationError

from backend.models.import_jobs import ImportJob, JobStatus

ASYNC_TASK_START_TEMPLATE = "Task started. Additional info: %s."
ASYNC_TASK_END_TEMPLATE = "Task ended."


def verify_no_other_import_jobs_running(current_job):
    # Method to verify that no other ImportJob tasks are running
    # on the provided site

    existing_incomplete_jobs = ImportJob.objects.filter(
        Q(site=current_job.site),
        Q(status__in=[JobStatus.ACCEPTED, JobStatus.STARTED])
        | Q(validation_status__in=[JobStatus.ACCEPTED, JobStatus.STARTED]),
    ).exclude(id=current_job.id)

    if len(existing_incomplete_jobs):
        raise ValidationError(
            "There is at least 1 job on this site that is already running or queued to run soon. "
            "Please wait for it to finish before starting a new one."
        )
