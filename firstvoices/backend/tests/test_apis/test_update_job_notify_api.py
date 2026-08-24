import pytest
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.models.import_jobs import ImportJobMode, ImportJobStatus
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_apis.test_import_job_notify_api import TestImportJobNotifyApi
from backend.tests.utils import get_sample_file


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
