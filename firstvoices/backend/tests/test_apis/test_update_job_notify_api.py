import json

import pytest
from django.core import mail

from backend.models.update_jobs import UpdateJob, UpdateJobStatus
from backend.tests import factories
from backend.tests.test_apis.base.import_update_jobs.base_notify_api_test import (
    BaseImportUpdateJobNotifyApi,
)
from backend.views.update_job_views import SUPPORT_USER_EMAIL


@pytest.mark.django_db
class TestUpdateJobNotifyApi(BaseImportUpdateJobNotifyApi):
    API_NOTIFY_ACTION = "api:updatejob-notify"
    SAMPLE_FILE_PATH = "update_job/all_valid_columns.csv"
    JOB_MODE = None
    JOB_MODEL = UpdateJob
    JOB_FACTORY = factories.UpdateJobFactory
    STATUS_ENUM = UpdateJobStatus
    JOB_ID_LABEL = "UpdateJob"
    NOT_VALIDATED_ERROR_MESSAGE = (
        "Please validate the job before marking it ready for processing."
    )
    ALREADY_READY_ERROR_MESSAGE = (
        "The update job is already marked ready for processing."
    )
    SUPPORT_EMAIL = SUPPORT_USER_EMAIL

    @pytest.mark.parametrize("validation_status", [None, UpdateJobStatus.COMPLETE])
    def test_cannot_notify_rolled_back_job(self, validation_status):
        self.job.status = UpdateJobStatus.ROLLED_BACK
        self.job.validation_status = validation_status
        self.job.save()

        response = self.client.post(self.get_notify_endpoint())

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == [
            "A rolled-back job cannot be marked ready for processing."
        ]
        self.job.refresh_from_db()
        assert self.job.status == UpdateJobStatus.ROLLED_BACK
        assert len(mail.outbox) == 0
