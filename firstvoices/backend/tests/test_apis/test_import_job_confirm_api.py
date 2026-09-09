import pytest

from backend.tests.test_apis.base.import_update_jobs.base_confirm_action_test import (
    BaseImportUpdateJobConfirmAction,
)


@pytest.mark.django_db(transaction=True)
class TestImportJobConfirmAction(BaseImportUpdateJobConfirmAction):
    API_CONFIRM_ACTION = "api:importjob-confirm"
    SAMPLE_FILE_PATH = "import_job/all_valid_columns.csv"
    COMPLETED_ERROR_MESSAGE = "This job has already finished importing."
    STARTED_ERROR_MESSAGE = (
        "This job has already been confirmed and is currently being imported."
    )
    NOT_VALIDATED_ERROR_MESSAGE = (
        "Please validate the job before confirming the import."
    )
