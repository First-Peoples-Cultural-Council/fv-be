import pytest

from backend.models.import_jobs import ImportJobMode
from backend.tests.test_apis.base.import_update_jobs.base_notify_api_test import (
    BaseImportUpdateJobNotifyApi,
)
from backend.views.update_job_views import SUPPORT_USER_EMAIL


@pytest.mark.django_db
class TestUpdateJobNotifyApi(BaseImportUpdateJobNotifyApi):
    API_NOTIFY_ACTION = "api:updatejob-notify"
    SAMPLE_FILE_PATH = "update_job/all_valid_columns.csv"
    JOB_MODE = ImportJobMode.UPDATE
    JOB_ID_LABEL = "UpdateJob"
    NOT_VALIDATED_ERROR_MESSAGE = (
        "Please validate the job before marking it ready for processing."
    )
    ALREADY_READY_ERROR_MESSAGE = (
        "The update job is already marked ready for processing."
    )
    SUPPORT_EMAIL = SUPPORT_USER_EMAIL
