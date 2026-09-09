import tablib
from rest_framework.exceptions import ValidationError

from backend.models.import_jobs import ImportJobStatus
from backend.tasks.constants import MAXIMUM_ENTRIES_PER_UPDATE_JOB


def verify_update_job_size_limit(current_job):
    # ensure the job data csv contains fewer entries than a set limit
    file = current_job.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")

    if len(data) > MAXIMUM_ENTRIES_PER_UPDATE_JOB:
        current_job.status = ImportJobStatus.FAILED
        current_job.save()
        raise ValidationError(
            f"The update job contains {len(data)} entries, "
            f"which exceeds the maximum allowed limit of {MAXIMUM_ENTRIES_PER_UPDATE_JOB} entries."
        )
