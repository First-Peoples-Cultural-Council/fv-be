import pytest
from django.core.exceptions import ValidationError

from backend.models.import_jobs import ImportJobReport
from backend.models.jobs import JobStatus
from backend.tests.factories import ImportJobFactory, ImportJobReportFactory


@pytest.mark.django_db
class TestImportJobModel:
    @pytest.mark.parametrize(
        "validation_status", [JobStatus.ACCEPTED, JobStatus.STARTED]
    )
    def test_delete_not_allowed_if_validation_started(self, validation_status):
        import_job = ImportJobFactory(validation_status=validation_status)
        with pytest.raises(ValidationError) as e:
            import_job.delete()
        assert "This job cannot be deleted as it is being validated." in e.value

    @pytest.mark.parametrize("status", [JobStatus.ACCEPTED, JobStatus.STARTED])
    def test_delete_not_allowed_if_import_started(self, status):
        import_job = ImportJobFactory(
            status=status, validation_status=JobStatus.COMPLETE
        )
        with pytest.raises(ValidationError) as e:
            import_job.delete()
        assert "This job cannot be deleted as it is being imported." in e.value

    def test_delete_not_allowed_if_job_is_complete(self):
        import_job = ImportJobFactory(
            status=JobStatus.COMPLETE, validation_status=JobStatus.COMPLETE
        )
        with pytest.raises(ValidationError) as e:
            import_job.delete()
        assert "A job that has been completed cannot be deleted." in e.value

    @pytest.mark.parametrize("add_report", [True, False])
    def test_report_is_deleted_if_exists_with_import_job_deletion(self, add_report):
        import_job = ImportJobFactory()

        if add_report:
            import_job.validation_report = ImportJobReportFactory()
            import_job.validation_status = JobStatus.COMPLETE
            import_job.save()

        import_job.delete()

        assert ImportJobReport.objects.count() == 0
