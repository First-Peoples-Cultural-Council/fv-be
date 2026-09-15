import pytest

from backend.models import ImportJobMode
from backend.tasks.update_job_tasks import validate_update_job
from backend.tests.test_apis.base.import_update_jobs.base_validate_action_test import (
    BaseImportUpdateJobValidateAction,
)


@pytest.mark.django_db(transaction=True)
class TestUpdateJobValidateAction(BaseImportUpdateJobValidateAction):
    API_LIST_VIEW = "api:updatejob-list"
    API_VALIDATE_ACTION = "api:updatejob-validate"
    SAMPLE_FILE_PATH = "update_job/all_valid_columns.csv"
    JOB_MODE = ImportJobMode.UPDATE
    VALIDATE_JOB_TASK = validate_update_job
    CONFIRMED_REVALIDATE_ERROR_MESSAGE = (
        "This job has already been confirmed and is currently being processed."
    )
