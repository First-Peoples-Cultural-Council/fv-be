import pytest

from backend.models.files import File
from backend.models.import_jobs import ImportJobStatus, RowStatus
from backend.models.media import ImageFile, VideoFile
from backend.models.update_jobs import (
    UpdateJobReport,
    UpdateJobRowStatus,
    UpdateJobStatus,
)
from backend.tests import factories


@pytest.mark.django_db
class TestUpdateJobModel:
    def test_status_values_match_import_job_statuses(self):
        assert UpdateJobStatus.values == ImportJobStatus.values

    def test_row_status_values_match_import_job_row_statuses(self):
        assert UpdateJobRowStatus.values == RowStatus.values

    @pytest.mark.parametrize("add_report", [True, False])
    def test_report_is_deleted_if_exists_with_update_job_deletion(self, add_report):
        update_job = factories.UpdateJobFactory.create()

        if add_report:
            update_job.validation_report = factories.UpdateJobReportFactory()
            update_job.validation_status = UpdateJobStatus.COMPLETE
            update_job.save()

        update_job.delete()

        assert UpdateJobReport.objects.count() == 0

    @pytest.mark.parametrize("add_failed_rows_csv", [True, False])
    def test_both_csvs_are_deleted_with_update_job_deletion(self, add_failed_rows_csv):
        update_job = factories.UpdateJobFactory.create()

        if add_failed_rows_csv:
            update_job.failed_rows_csv = factories.FileFactory.create()
            update_job.save()

        update_job.delete()

        assert File.objects.count() == 0

    def test_delete_uploaded_media(self):
        update_job = factories.UpdateJobFactory.create()

        factories.FileFactory.create(update_job=update_job)
        factories.ImageFileFactory.create(update_job=update_job)
        factories.VideoFileFactory.create(update_job=update_job)

        assert File.objects.count() == 2
        assert ImageFile.objects.count() == 1
        assert VideoFile.objects.count() == 1

        update_job.delete()

        assert File.objects.count() == 0
        assert ImageFile.objects.count() == 0
        assert VideoFile.objects.count() == 0

    def test_update_job_relationships(self):
        update_job = factories.UpdateJobFactory.create()
        entry = factories.DictionaryEntryFactory.create(update_job=update_job)
        file = factories.FileFactory.create(update_job=update_job)
        image = factories.ImageFileFactory.create(update_job=update_job)
        video = factories.VideoFileFactory.create(update_job=update_job)

        assert entry.update_job == update_job
        assert file.update_job == update_job
        assert image.update_job == update_job
        assert video.update_job == update_job
