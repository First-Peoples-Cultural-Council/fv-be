import pytest

from backend.models.files import File
from backend.models.import_jobs import ImportJobReport
from backend.models.jobs import JobStatus
from backend.models.media import ImageFile, VideoFile
from backend.tests import factories


@pytest.mark.django_db
class TestImportJobModel:
    @pytest.mark.parametrize("add_report", [True, False])
    def test_report_is_deleted_if_exists_with_import_job_deletion(self, add_report):
        import_job = factories.ImportJobFactory.create()

        if add_report:
            import_job.validation_report = factories.ImportJobReportFactory()
            import_job.validation_status = JobStatus.COMPLETE
            import_job.save()

        import_job.delete()

        assert ImportJobReport.objects.count() == 0

    @pytest.mark.django_db
    @pytest.mark.parametrize("add_failed_rows_csv", [True, False])
    def test_both_csvs_are_deleted_with_import_job_deletion(self, add_failed_rows_csv):
        import_job = factories.ImportJobFactory.create()

        if add_failed_rows_csv:
            import_job.failed_rows_csv = factories.FileFactory.create()
            import_job.save()

        import_job.delete()

        assert File.objects.count() == 0

    @pytest.mark.django_db
    def test_delete_uploaded_media(self):
        import_job = factories.ImportJobFactory.create()

        factories.FileFactory.create(import_job=import_job)
        factories.ImageFileFactory.create(import_job=import_job)
        factories.VideoFileFactory.create(import_job=import_job)

        assert File.objects.count() == 2  # 1 audio + 1 data csv
        assert ImageFile.objects.count() == 1
        assert VideoFile.objects.count() == 1

        import_job.delete()

        assert File.objects.count() == 0
        assert ImageFile.objects.count() == 0
        assert VideoFile.objects.count() == 0
