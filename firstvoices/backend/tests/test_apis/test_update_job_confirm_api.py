import json

import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models import ImportJobMode
from backend.models.constants import Role, Visibility
from backend.models.jobs import JobStatus
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_apis.test_import_job_confirm_api import (
    TestImportJobConfirmAction,
)
from backend.tests.utils import get_sample_file


@pytest.mark.django_db(transaction=True)
class TestUpdateJobConfirmAction(TestImportJobConfirmAction):
    """
    Tests for the update-jobs API confirm action. Subclasses
    the base import-job confirm tests and overrides methods as necessary.
    """

    API_CONFIRM_ACTION = "api:updatejob-confirm"

    def create_import_job(
        self, site, status=None, validation_status=JobStatus.COMPLETE
    ):
        return ImportJobFactory(
            site=site,
            data=factories.FileFactory(
                content=get_sample_file("update_job/all_valid_columns.csv", "text/csv")
            ),
            validation_status=validation_status,
            status=status,
            mode=ImportJobMode.UPDATE,
        )

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
            validation_status=JobStatus.COMPLETE,
            mode=ImportJobMode.UPDATE,
        )

    def test_reconfirming_a_completed_job_not_allowed(self):
        import_job = self.create_import_job(site=self.site, status=JobStatus.COMPLETE)

        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(import_job.id)],
        )
        response = self.client.post(confirm_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert "This job has already finished processing." in response

    @pytest.mark.parametrize("status", [JobStatus.ACCEPTED, JobStatus.STARTED])
    def test_confirming_already_started_or_queued_job_not_allowed(self, status):
        self.import_job.status = JobStatus.COMPLETE
        self.import_job.save()

        import_job = self.create_import_job(site=self.site, status=status)

        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(import_job.id)],
        )
        response = self.client.post(confirm_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "This job has already been confirmed and is currently being processed."
            in response
        )

    @pytest.mark.parametrize(
        "validation_status",
        [None, JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.FAILED],
    )
    def test_confirm_only_allowed_for_completed_dry_run(self, validation_status):
        self.import_job.validation_status = validation_status
        self.import_job.save()

        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(self.import_job.id)],
        )
        response = self.client.post(confirm_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert "Please validate the job before confirming the update job." in response
