import pytest

from backend.models import ImportJob
from backend.models.constants import Visibility
from backend.tasks.import_job_tasks import execute_dry_run_import
from backend.tests.factories import FileFactory, ImportJobFactory, SiteFactory
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestDryRunImport:
    MIMETYPE = "text/csv"

    def test_import_task_logs(self, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file(
            "import_job/import_job_minimal.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        execute_dry_run_import(import_job_instance.id)

        assert (
            f"Task started. Additional info: import_job_instance_id: {import_job_instance.id}."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_base_case_dictionary_entries(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        execute_dry_run_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report

        assert validation_report.new_rows == 2
        assert validation_report.error_rows == 0
        assert validation_report.skipped_rows == 0

    def test_all_columns_dictionary_entries(self):
        # More columns could be added to this file/test later
        # as we start supporting more columns, e.g. related_media

        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file(
            "import_job/all_valid_columns.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        execute_dry_run_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report

        assert validation_report.new_rows == 4
        assert validation_report.error_rows == 0
        assert validation_report.skipped_rows == 0

    def test_invalid_rows(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file(
            "import_job/invalid_dictionary_entries.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        execute_dry_run_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report
        error_rows = validation_report.rows.all()
        error_rows_numbers = list(
            validation_report.rows.values_list("row_number", flat=True)
        )

        assert len(error_rows) == 4
        assert error_rows_numbers == [1, 3, 4, 5]

    def test_invalid_categories(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file(
            "import_job/invalid_categories.csv", self.MIMETYPE
        )  # 1st row in the file a valid row for control
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        execute_dry_run_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report
        error_rows = validation_report.rows.all()
        error_rows_numbers = list(
            validation_report.rows.values_list("row_number", flat=True)
        )

        assert len(error_rows) == 4
        assert error_rows_numbers == [2, 3, 4, 5]

    def test_validation_report_columns(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file("import_job/unknown_columns.csv", self.MIMETYPE)
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        execute_dry_run_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report
        accepted_columns = validation_report.accepted_columns
        ignored_columns = validation_report.ignored_columns

        assert "abc" in ignored_columns
        assert "xyz" in ignored_columns

        assert "title" in accepted_columns
        assert "type" in accepted_columns
