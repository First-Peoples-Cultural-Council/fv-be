import pytest

from backend.models.update_jobs import UpdateJob
from backend.tasks.update_job_tasks import validate_update_job
from backend.tests import factories
from backend.tests.test_apis.base.import_update_jobs.base_validate_action_test import (
    BaseImportUpdateJobValidateAction,
)


@pytest.mark.django_db(transaction=True)
class TestUpdateJobValidateAction(BaseImportUpdateJobValidateAction):
    API_LIST_VIEW = "api:updatejob-list"
    API_VALIDATE_ACTION = "api:updatejob-validate"
    SAMPLE_FILE_PATH = "update_job/all_valid_columns.csv"
    JOB_MODE = None
    JOB_MODEL = UpdateJob
    JOB_FACTORY = factories.UpdateJobFactory
    REPORT_FILTER_PATCH_PATH = (
        "backend.tasks.utils.reporting_utils.UpdateJobReport.objects.filter"
    )
    JOB_LOG_LABEL = "update_job"
    VALIDATE_JOB_TASK = validate_update_job
    CONFIRMED_REVALIDATE_ERROR_MESSAGE = (
        "This job has already been confirmed and is currently being processed."
    )
