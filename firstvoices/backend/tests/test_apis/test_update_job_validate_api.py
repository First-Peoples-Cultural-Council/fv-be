import pytest

from backend.models import ImportJobMode
from backend.tests.test_apis.test_import_job_validate_api import (
    TestImportJobValidateAction,
)


@pytest.mark.django_db(transaction=True)
class TestUpdateJobValidateAction(TestImportJobValidateAction):
    """
    Tests for the update-jobs API validate action. Subclasses
    the base import-job validate tests and overrides methods as necessary.
    """

    API_LIST_VIEW = "api:updatejob-list"
    API_VALIDATE_ACTION = "api:updatejob-validate"
    SAMPLE_FILE_PATH = "update_job/all_valid_columns.csv"
    JOB_MODE = ImportJobMode.UPDATE
    CONFIRMED_REVALIDATE_ERROR_MESSAGE = (
        "This job has already been confirmed and is currently being processed."
    )
