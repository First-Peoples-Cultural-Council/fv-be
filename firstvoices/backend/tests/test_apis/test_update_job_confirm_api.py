import pytest
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

    def create_import_job(self, site, status=None):
        return ImportJobFactory(
            site=site,
            data=factories.FileFactory(
                content=get_sample_file("update_job/all_valid_columns.csv", "text/csv")
            ),
            validation_status=JobStatus.COMPLETE,
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
