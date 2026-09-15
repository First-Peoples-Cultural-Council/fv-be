import json

import pytest
from django.core import mail
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.models.import_jobs import ImportJob, ImportJobStatus
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
)
from backend.tests.utils import get_sample_file
from backend.views.import_job_views import SUPPORT_USER_EMAIL


@pytest.mark.django_db
class TestImportJobNotifyApi(BaseSiteContentApiTest):
    API_NOTIFY_ACTION = "api:importjob-notify"
    SAMPLE_FILE_PATH = "import_job/all_valid_columns.csv"
    JOB_MODE = None
    JOB_ID_LABEL = "ImportJob"
    NOT_VALIDATED_ERROR_MESSAGE = (
        "Please validate the job before marking it ready for import."
    )
    ALREADY_READY_ERROR_MESSAGE = "The import-job is already marked ready for import."
    SUPPORT_EMAIL = SUPPORT_USER_EMAIL

    def get_job_mode_kwargs(self):
        if self.JOB_MODE is None:
            return {}
        return {"mode": self.JOB_MODE}

    def create_minimal_instance(self, site, visibility):
        # Not required for this endpoint
        return {}

    def get_expected_response(self, instance, site):
        # Not required for this endpoint
        return {}

    def setup_method(self):
        self.client = APIClient()
        self.site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        file_content = get_sample_file(self.SAMPLE_FILE_PATH, "text/csv")
        file = factories.FileFactory(content=file_content)
        self.import_job = ImportJobFactory(
            site=self.site,
            data=file,
            validation_status=ImportJobStatus.COMPLETE,
            **self.get_job_mode_kwargs(),
        )

    def test_notify_sends_email_to_support(self):
        assert len(mail.outbox) == 0

        url = reverse(
            self.API_NOTIFY_ACTION, args=[self.site.slug, str(self.import_job.id)]
        )

        response = self.client.post(url)

        assert response.status_code == 202

        assert len(mail.outbox) == 1

        assert mail.outbox[0].to == [self.SUPPORT_EMAIL]

        assert f"Site slug: {self.site.slug}" in mail.outbox[0].body
        assert f"{self.JOB_ID_LABEL} id: {self.import_job.id}" in mail.outbox[0].body

    def test_notify_updates_job_status_to_ready(self):
        url = reverse(
            self.API_NOTIFY_ACTION, args=[self.site.slug, str(self.import_job.id)]
        )

        response = self.client.post(url)

        assert response.status_code == 202

        import_job = ImportJob.objects.get(id=self.import_job.id)
        assert import_job.status == ImportJobStatus.READY_FOR_IMPORT

    @pytest.mark.parametrize(
        "validation_status",
        [
            None,
            ImportJobStatus.ACCEPTED,
            ImportJobStatus.STARTED,
            ImportJobStatus.FAILED,
            ImportJobStatus.CANCELLED,
        ],
    )
    def test_notify_job_only_works_on_validated_jobs(self, validation_status):
        self.import_job.validation_status = validation_status
        self.import_job.save()

        notify_endpoint = reverse(
            self.API_NOTIFY_ACTION, args=[self.site.slug, str(self.import_job.id)]
        )
        response = self.client.post(notify_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert self.NOT_VALIDATED_ERROR_MESSAGE in response

    def test_cannot_mark_a_test_already_marked_READY_FOR_IMPORT(self):
        self.import_job.status = ImportJobStatus.READY_FOR_IMPORT
        self.import_job.save()

        notify_endpoint = reverse(
            self.API_NOTIFY_ACTION, args=[self.site.slug, str(self.import_job.id)]
        )
        response = self.client.post(notify_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)

        assert self.ALREADY_READY_ERROR_MESSAGE in response
