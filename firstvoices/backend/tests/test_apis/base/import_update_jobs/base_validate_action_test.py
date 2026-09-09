import json
from unittest.mock import MagicMock, patch

import pytest
from django.utils.http import urlencode
from rest_framework.reverse import reverse

from backend.models import ImportJob
from backend.models.constants import AppRole, Visibility
from backend.models.jobs import JobStatus
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_apis.base.base_media_test import FormDataMixin
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
)
from backend.tests.utils import get_sample_file


class BaseImportUpdateJobValidateAction(FormDataMixin, BaseSiteContentApiTest):
    API_LIST_VIEW = None
    API_VALIDATE_ACTION = None
    SAMPLE_FILE_PATH = None
    JOB_MODE = None
    VALIDATE_JOB_TASK = None
    CONFIRMED_REVALIDATE_ERROR_MESSAGE = None

    def get_job_mode_kwargs(self):
        if self.JOB_MODE is None:
            return {}
        return {"mode": self.JOB_MODE}

    def create_minimal_instance(self, site, visibility):
        return {}

    def get_expected_response(self, instance, site):
        return {}

    def get_list_endpoint(self, site_slug=None, query_kwargs=None):
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

        file_content = get_sample_file(self.SAMPLE_FILE_PATH, "text/csv")
        file = factories.FileFactory(content=file_content)
        self.job = ImportJobFactory(
            site=self.site,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            **self.get_job_mode_kwargs(),
        )
        self.VALIDATE_JOB_TASK(self.job.id)

    def get_validate_endpoint(self, job):
        return reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(job.id)],
        )

    def test_exception_fetching_previous_report(self, caplog):
        mock_report = MagicMock()
        mock_report.delete.side_effect = Exception("General Exception")
        with patch(
            "backend.tasks.utils.reporting_utils.ImportJobReport.objects.filter",
            return_value=mock_report,
        ):
            response = self.client.post(self.get_validate_endpoint(self.job))

        job = ImportJob.objects.filter(id=self.job.id).first()

        assert response.status_code == 202
        assert "General Exception" in caplog.text
        assert (
            f"Unable to delete previous report for import_job: {str(job.id)}"
            in caplog.text
        )

    def test_validate_action(self):
        job = ImportJob.objects.get(id=self.job.id)
        old_validation_report_id = job.validation_report.id

        response = self.client.post(self.get_validate_endpoint(job))

        assert response.status_code == 202
        job.refresh_from_db()
        assert job.validation_report.id != old_validation_report_id

    def test_more_than_one_jobs_not_allowed(self):
        ImportJobFactory(
            site=self.site,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.STARTED,
        )

        response = self.client.post(self.get_validate_endpoint(self.job))

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            "There is at least 1 job on this site that is already running or queued to run soon. Please wait for "
            "it to finish before starting a new one." in response_data
        )

    @pytest.mark.parametrize(
        "validation_status", [JobStatus.ACCEPTED, JobStatus.STARTED]
    )
    def test_validating_current_job_again_not_allowed(self, validation_status):
        ImportJob.objects.filter(id=self.job.id).delete()
        job = ImportJobFactory(
            site=self.site,
            validation_status=validation_status,
            **self.get_job_mode_kwargs(),
        )

        response = self.client.post(self.get_validate_endpoint(job))

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            "This job has already been queued and is currently being validated."
            in response_data
        )

    @pytest.mark.parametrize(
        "status", [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE]
    )
    def test_confirmed_job_not_allowed_to_revalidate(self, status):
        self.job.status = status
        self.job.validation_status = None
        self.job.save()

        response = self.client.post(self.get_validate_endpoint(self.job))

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert self.CONFIRMED_REVALIDATE_ERROR_MESSAGE in response_data
