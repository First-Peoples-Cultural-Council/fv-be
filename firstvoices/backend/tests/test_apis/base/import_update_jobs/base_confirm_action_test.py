import json

import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.models.import_jobs import ImportJobStatus
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
)
from backend.tests.utils import get_sample_file


class BaseImportUpdateJobConfirmAction(BaseSiteContentApiTest):
    API_CONFIRM_ACTION = None
    SAMPLE_FILE_PATH = None
    JOB_MODE = None
    COMPLETED_ERROR_MESSAGE = None
    STARTED_ERROR_MESSAGE = None
    NOT_VALIDATED_ERROR_MESSAGE = None

    def create_minimal_instance(self, site, visibility):
        return {}

    def get_expected_response(self, instance, site):
        return {}

    def get_job_mode_kwargs(self):
        if self.JOB_MODE is None:
            return {}
        return {"mode": self.JOB_MODE}

    def create_job(self, site, status=None, validation_status=ImportJobStatus.COMPLETE):
        return ImportJobFactory(
            site=site,
            data=factories.FileFactory(
                content=get_sample_file(self.SAMPLE_FILE_PATH, "text/csv")
            ),
            validation_status=validation_status,
            status=status,
            **self.get_job_mode_kwargs(),
        )

    def setup_method(self):
        self.client = APIClient()
        self.site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)
        self.job = self.create_job(site=self.site)

    def get_confirm_endpoint(self, job):
        return reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(job.id)],
        )

    def test_confirm_action(self):
        response = self.client.post(self.get_confirm_endpoint(self.job))

        assert response.status_code == 202

    @pytest.mark.parametrize(
        "status", [ImportJobStatus.ACCEPTED, ImportJobStatus.STARTED]
    )
    def test_more_than_one_jobs_not_allowed(self, status):
        self.job.status = status
        self.job.save()
        other_job = self.create_job(site=self.site)

        response = self.client.post(self.get_confirm_endpoint(other_job))

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            "There is at least 1 job on this site that is already running or queued to run soon. Please wait for "
            "it to finish before starting a new one." in response_data
        )

    def test_reconfirming_a_completed_job_not_allowed(self):
        job = self.create_job(site=self.site, status=ImportJobStatus.COMPLETE)

        response = self.client.post(self.get_confirm_endpoint(job))

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert self.COMPLETED_ERROR_MESSAGE in response_data

    @pytest.mark.parametrize(
        "status", [ImportJobStatus.ACCEPTED, ImportJobStatus.STARTED]
    )
    def test_confirming_already_started_or_queued_job_not_allowed(self, status):
        self.job.status = ImportJobStatus.COMPLETE
        self.job.save()
        job = self.create_job(site=self.site, status=status)

        response = self.client.post(self.get_confirm_endpoint(job))

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert self.STARTED_ERROR_MESSAGE in response_data

    @pytest.mark.parametrize(
        "validation_status",
        [
            None,
            ImportJobStatus.ACCEPTED,
            ImportJobStatus.STARTED,
            ImportJobStatus.FAILED,
        ],
    )
    def test_confirm_only_allowed_for_completed_dry_run(self, validation_status):
        self.job.validation_status = validation_status
        self.job.save()

        response = self.client.post(self.get_confirm_endpoint(self.job))

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert self.NOT_VALIDATED_ERROR_MESSAGE in response_data
