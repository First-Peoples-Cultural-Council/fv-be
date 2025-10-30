import json

import pytest
from rest_framework.reverse import reverse

from backend.models import ImportJob, ImportJobMode
from backend.models.constants import AppRole, Visibility
from backend.models.jobs import JobStatus
from backend.tasks.import_job_tasks import validate_import_job
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_apis.test_import_job_validate_api import (
    TestImportJobValidateAction,
)
from backend.tests.utils import get_sample_file


@pytest.mark.django_db(transaction=True)
class TestUpdateJobValidateAction(TestImportJobValidateAction):
    """
    Tests for the update-jobs API validate action. Subclasses
    the base import-job validate tests and overrides methods as necessary.
    """

    API_LIST_VIEW = "api:updatejob-list"
    API_VALIDATE_ACTION = "api:updatejob-validate"

    def setup_method(self):
        super().setup_method()

        user = factories.UserFactory.create()
        factories.AppMembershipFactory.create(user=user, role=AppRole.SUPERADMIN)

        self.client.force_authenticate(user=user)
        self.site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        # Initial job
        file_content = get_sample_file("update_job/all_valid_columns.csv", "text/csv")
        file = factories.FileFactory(content=file_content)
        self.import_job = ImportJobFactory(
            site=self.site,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )
        validate_import_job(self.import_job.id)

    @pytest.mark.parametrize(
        "validation_status", [JobStatus.ACCEPTED, JobStatus.STARTED]
    )
    def test_validating_current_job_again_not_allowed(self, validation_status):
        ImportJob.objects.filter(id=self.import_job.id).delete()

        import_job = ImportJobFactory(
            site=self.site,
            validation_status=validation_status,
            mode=ImportJobMode.UPDATE,
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
