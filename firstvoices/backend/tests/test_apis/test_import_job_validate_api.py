import json
from unittest.mock import MagicMock, patch

import pytest
from django.utils.http import urlencode
from rest_framework.reverse import reverse

from backend.models import ImportJob
from backend.models.constants import AppRole, Visibility
from backend.models.jobs import JobStatus
from backend.tasks.import_job_tasks import validate_import_job
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_apis.base.base_media_test import FormDataMixin
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
)
from backend.tests.utils import get_sample_file


@pytest.mark.django_db(transaction=True)
class TestImportJobValidateAction(FormDataMixin, BaseSiteContentApiTest):
    API_LIST_VIEW = "api:importjob-list"
    API_VALIDATE_ACTION = "api:importjob-validate"

    def create_minimal_instance(self, site, visibility):
        # Not required for this endpoint
        return {}

    def get_expected_response(self, instance, site):
        # Not required for this endpoint
        return {}

    def get_list_endpoint(self, site_slug=None, query_kwargs=None):
        """
        query_kwargs accept query parameters e.g. query_kwargs={"contains": "WORD"}
        """
        url = reverse(self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug])
        if query_kwargs:
            return f"{url}?{urlencode(query_kwargs)}"
        return url

    def setup_method(self):
        super().setup_method()

        user = factories.UserFactory.create()
        factories.AppMembershipFactory.create(user=user, role=AppRole.SUPERADMIN)

        self.client.force_authenticate(user=user)
        self.site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        # Initial job
        file_content = get_sample_file("import_job/all_valid_columns.csv", "text/csv")
        file = factories.FileFactory(content=file_content)
        self.import_job = ImportJobFactory(
            site=self.site, data=file, validation_status=JobStatus.ACCEPTED
        )
        validate_import_job(self.import_job.id)

    def test_exception_fetching_previous_report(self, caplog):
        # Simulating a general exception when fetching/deleting a previous
        # validation report

        mock_report = MagicMock()
        mock_report.delete.side_effect = Exception("General Exception")
        with patch(
            "backend.tasks.import_job_tasks.ImportJobReport.objects.filter",
            return_value=mock_report,
        ):
            validate_endpoint = reverse(
                self.API_VALIDATE_ACTION,
                current_app=self.APP_NAME,
                args=[self.site.slug, str(self.import_job.id)],
            )

            response = self.client.post(validate_endpoint)

        # Updating import-job instance in memory
        import_job = ImportJob.objects.filter(id=self.import_job.id).first()

        assert response.status_code == 202

        assert "General Exception" in caplog.text
        assert (
            f"Unable to delete previous report for import_job: {str(import_job.id)}"
            in caplog.text
        )

    def test_validate_action(self):
        import_job = ImportJob.objects.filter(id=self.import_job.id)[0]
        old_validation_report_id = import_job.validation_report.id

        validate_endpoint = reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(self.import_job.id)],
        )
        response = self.client.post(validate_endpoint)
        assert response.status_code == 202

        import_job = ImportJob.objects.filter(id=self.import_job.id)[0]
        new_validation_report_id = import_job.validation_report.id

        assert new_validation_report_id != old_validation_report_id

    def test_more_than_one_jobs_not_allowed(self):
        ImportJobFactory(
            site=self.site,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.STARTED,
        )  # second job

        validate_endpoint = reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(self.import_job.id)],
        )
        response = self.client.post(validate_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "There is at least 1 job on this site that is already running or queued to run soon. Please wait for "
            "it to finish before starting a new one." in response
        )

    @pytest.mark.parametrize(
        "validation_status", [JobStatus.ACCEPTED, JobStatus.STARTED]
    )
    def test_validating_current_job_again_not_allowed(self, validation_status):
        # removing the job created in setup method
        ImportJob.objects.filter(id=self.import_job.id).delete()

        import_job = ImportJobFactory(
            site=self.site,
            validation_status=validation_status,
        )

        # Validate endpoint
        validate_endpoint = reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(import_job.id)],
        )

        response = self.client.post(validate_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "This job has already been queued and is currently being validated."
            in response
        )

    @pytest.mark.parametrize(
        "status",
        [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE],
    )
    def test_confirmed_job_not_allowed_to_revalidate(self, status):
        self.import_job.status = status
        self.import_job.validation_status = None
        self.import_job.save()

        # Validate endpoint
        validate_endpoint = reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(self.import_job.id)],
        )

        response = self.client.post(validate_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "This job has already been confirmed and is currently being imported."
            in response
        )
