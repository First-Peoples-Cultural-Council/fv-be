import pytest
from django.core.exceptions import ValidationError

from backend.models.import_jobs import ImportJobReport
from backend.models.jobs import JobStatus
from backend.tests.factories import ImportJobFactory, ImportJobReportFactory


@pytest.mark.django_db
class TestImportJobModel:
    def test_delete_not_allowed_if_job_is_complete(self):
        import_job = ImportJobFactory(status=JobStatus.COMPLETE)
        with pytest.raises(ValidationError) as e:
            import_job.delete()
        assert "A job that has been completed cannot be deleted." in e.value

    def test_report_is_deleted_when_import_job_is_deleted(self):
        import_job_report = ImportJobReportFactory()
        import_job = ImportJobFactory(validation_report=import_job_report)

        import_job.delete()

        assert len(ImportJobReport.objects.filter(id=import_job_report.id)) == 0
