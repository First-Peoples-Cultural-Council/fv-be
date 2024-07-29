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

        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
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
        accepted_columns = validation_report.accepted_columns
        ignored_columns = validation_report.ignored_columns

        assert validation_report.new_rows == 4
        assert validation_report.error_rows == 0
        assert validation_report.skipped_rows == 0

        expected_valid_columns = [
            "title",
            "type",
            "visibility",
            "include_in_games",
            "include_on_kids_site",
            "translation",
            "translation_2",
            "translation_3",
            "translation_4",
            "translation_5",
            "acknowledgement",
            "acknowledgement_2",
            "acknowledgement_3",
            "acknowledgement_4",
            "acknowledgement_5",
            "note",
            "note_2",
            "note_3",
            "note_4",
            "note_5",
            "alternate_spelling",
            "alternate_spelling_2",
            "alternate_spelling_3",
            "alternate_spelling_4",
            "alternate_spelling_5",
            "category",
            "category_2",
            "category_3",
            "category_4",
            "category_5",
            "part_of_speech",
            "pronunciation",
            "pronunciation_2",
            "pronunciation_3",
            "pronunciation_4",
            "pronunciation_5",
        ]

        for column in expected_valid_columns:
            assert column in accepted_columns

        assert len(ignored_columns) == 0

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
            validation_report.rows.order_by("row_number").values_list(
                "row_number", flat=True
            )
        )

        assert len(error_rows) == 5
        assert error_rows_numbers == [2, 3, 4, 5, 6]

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

    def test_missing_original_column(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file(
            "import_job/original_header_missing.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        execute_dry_run_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report
        accepted_columns = validation_report.accepted_columns
        ignored_columns = validation_report.ignored_columns

        assert "note_2" in ignored_columns
        assert "note_3" in ignored_columns

        assert "title" in accepted_columns
        assert "type" in accepted_columns

    def test_boolean_variations(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file(
            "import_job/boolean_variations.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        execute_dry_run_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report

        assert validation_report.new_rows == 12
        assert validation_report.error_rows == 0
        assert validation_report.skipped_rows == 0
