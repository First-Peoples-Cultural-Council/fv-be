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
    API_CONFIRM_ACTION = "api:importjob-notify"

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

        file_content = get_sample_file("import_job/all_valid_columns.csv", "text/csv")
        file = factories.FileFactory(content=file_content)
        self.import_job = ImportJobFactory(
            site=self.site, data=file, validation_status=ImportJobStatus.COMPLETE
        )

    def test_notify_sends_email_to_support(self):
        assert len(mail.outbox) == 0

        url = reverse(
            "api:importjob-notify",
            kwargs={"site_slug": self.site.slug, "pk": self.import_job.id},
        )

        response = self.client.post(url)

        assert response.status_code == 202

        assert len(mail.outbox) == 1

        assert mail.outbox[0].to == [SUPPORT_USER_EMAIL]

        assert f"Site slug: {self.site.slug}" in mail.outbox[0].body
        assert f"ImportJob id: {self.import_job.id}" in mail.outbox[0].body

    def test_notify_updates_job_status_to_ready(self):
        url = reverse(
            "api:importjob-notify",
            kwargs={"site_slug": self.site.slug, "pk": self.import_job.id},
        )

        response = self.client.post(url)

        assert response.status_code == 202

        import_job = ImportJob.objects.get(id=self.import_job.id)
        assert import_job.status == ImportJobStatus.READY_FOR_IMPORT
