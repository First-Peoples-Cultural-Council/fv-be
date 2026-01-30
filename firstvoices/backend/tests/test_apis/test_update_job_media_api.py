import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.tests.factories import FileFactory, ImportJobFactory, get_site_with_member
from backend.tests.test_apis.test_import_job_media_api import TestImportJobMediaEndpoint
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestUpdateJobMediaEndpoint(
    TestImportJobMediaEndpoint,
):
    APP_NAME = "backend"
    UPLOAD_VIEW = "api:updatejob-media-list"

    def setup_method(self):
        self.site, self.user = get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )

        file_content = get_sample_file("update_job/minimal.csv", "text/csv")
        file = FileFactory(content=file_content)
        self.import_job = ImportJobFactory(site=self.site, data=file)

        self.endpoint = reverse(
            self.UPLOAD_VIEW,
            current_app=self.APP_NAME,
            args=[self.site.slug, self.import_job.id],
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
