import pytest

from backend.models.constants import Visibility
from backend.models.files import File
from backend.models.jobs import (
    BulkVisibilityJob,
    DictionaryCleanupJob,
    ExportJob,
    JobStatus,
)
from backend.tests import factories


class TestDictionaryCleanupJobModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        test_job = DictionaryCleanupJob.objects.create(site=site)

        expected_str = f"{site.title} - DictionaryCleanup - {str(test_job.id)}"
        assert str(test_job) == expected_str


class TestBulkVisibilityJobModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        test_entry = BulkVisibilityJob.objects.create(
            site=site,
            task_id="abc123",
            status=JobStatus.ACCEPTED,
            from_visibility=Visibility.PUBLIC,
            to_visibility=Visibility.PUBLIC,
        )

        expected_str = f"{site.title} - BulkVisibility - {test_entry.status}"
        assert str(test_entry) == expected_str


class TestExportJobModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        test_export = ExportJob.objects.create(
            site=site,
            task_id="abc123",
            status=JobStatus.ACCEPTED,
        )
        expected_str = f"{site.title} Export Job (id: {str(test_export.id)})"

        assert str(test_export) == expected_str

    @pytest.mark.django_db
    @pytest.mark.parametrize("add_export_job_csv", [True, False])
    def test_deletion_export_csv(self, add_export_job_csv):
        export_job = factories.ExportJobFactory.create()

        if add_export_job_csv:
            export_job.export_csv = factories.FileFactory.create()
            export_job.save()

        export_job.delete()

        assert File.objects.count() == 0
