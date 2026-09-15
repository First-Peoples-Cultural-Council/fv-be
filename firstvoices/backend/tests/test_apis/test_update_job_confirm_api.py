import pytest

from backend.models import ImportJobMode
from backend.tests.test_apis.base.import_update_jobs.base_confirm_action_test import (
    BaseImportUpdateJobConfirmAction,
)


@pytest.mark.django_db(transaction=True)
class TestUpdateJobConfirmAction(BaseImportUpdateJobConfirmAction):
    API_CONFIRM_ACTION = "api:updatejob-confirm"
    SAMPLE_FILE_PATH = "update_job/all_valid_columns.csv"
    JOB_MODE = ImportJobMode.UPDATE
    COMPLETED_ERROR_MESSAGE = "This job has already finished processing."
    STARTED_ERROR_MESSAGE = (
        "This job has already been confirmed and is currently being processed."
    )
    NOT_VALIDATED_ERROR_MESSAGE = (
        "Please validate the job before confirming the update job."
    )
