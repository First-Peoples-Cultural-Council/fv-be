import pytest

from backend.models.constants import Visibility
from backend.models.jobs import BulkVisibilityJob, DictionaryCleanupJob, JobStatus
from backend.tests.factories import SiteFactory


class TestDictionaryCleanupJobModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        test_job = DictionaryCleanupJob.objects.create(site=site)

        expected_str = f"{site.title} - DictionaryCleanup - {test_job.status}"
        assert str(test_job) == expected_str


class TestBulkVisibilityJobModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        test_entry = BulkVisibilityJob.objects.create(
            site=site,
            task_id="abc123",
            status=JobStatus.ACCEPTED,
            from_visibility=Visibility.PUBLIC,
            to_visibility=Visibility.PUBLIC,
        )

        expected_str = f"{site.title} - BulkVisibility - {test_entry.status}"
        assert str(test_entry) == expected_str
