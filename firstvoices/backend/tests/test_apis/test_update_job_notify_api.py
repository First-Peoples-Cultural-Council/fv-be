import json

import pytest
from django.core import mail
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.models.import_jobs import ImportJobMode, ImportJobStatus
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_apis.test_import_job_notify_api import TestImportJobNotifyApi
from backend.tests.utils import get_sample_file
from backend.views.update_job_views import SUPPORT_USER_EMAIL


@pytest.mark.django_db
class TestUpdateJobNotifyApi(TestImportJobNotifyApi):
    API_NOTIFY_ACTION = "api:updatejob-notify"

    def setup_method(self):
        self.client = APIClient()
        self.site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        file_content = get_sample_file("update_job/all_valid_columns.csv", "text/csv")
        file = factories.FileFactory(content=file_content)
        self.import_job = ImportJobFactory(
            site=self.site,
            data=file,
            validation_status=ImportJobStatus.COMPLETE,
            mode=ImportJobMode.UPDATE,
        )

    def test_notify_sends_email_to_support(self):
        assert len(mail.outbox) == 0

        url = reverse(
            self.API_NOTIFY_ACTION, args=[self.site.slug, str(self.import_job.id)]
        )

        response = self.client.post(url)

        assert response.status_code == 202

        assert len(mail.outbox) == 1

        assert mail.outbox[0].to == [SUPPORT_USER_EMAIL]

        assert f"Site slug: {self.site.slug}" in mail.outbox[0].body
        assert f"UpdateJob id: {self.import_job.id}" in mail.outbox[0].body

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
        assert (
            "Please validate the job before marking it ready for processing."
            in response
        )

    def test_cannot_mark_a_test_already_marked_READY_FOR_IMPORT(self):
        self.import_job.status = ImportJobStatus.READY_FOR_IMPORT
        self.import_job.save()

        notify_endpoint = reverse(
            self.API_NOTIFY_ACTION, args=[self.site.slug, str(self.import_job.id)]
        )
        response = self.client.post(notify_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)

        assert "The update job is already marked ready for processing." in response
