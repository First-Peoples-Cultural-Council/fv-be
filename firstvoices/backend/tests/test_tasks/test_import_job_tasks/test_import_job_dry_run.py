import pytest

from backend.models import ImportJob
from backend.models.constants import Visibility
from backend.models.import_jobs import JobStatus
from backend.tasks.import_job_tasks import validate_import_job
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportJobDryRun:
    MIMETYPE = "text/csv"
    MEDIA_FILES_DIR = "test_tasks/test_import_job_tasks/resources"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def test_task_logs(self, caplog):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_task_logs.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        assert (
            f"Task started. Additional info: ImportJob id: {import_job.id}, dry-run: True."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_unknown_columns(self):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_unknown_columns.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        accepted_columns = validation_report.accepted_columns
        ignored_columns = validation_report.ignored_columns

        assert "unknown_column_1" in ignored_columns
        assert "unknown_column_2" in ignored_columns

        assert "title" in accepted_columns
        assert "type" in accepted_columns

    def test_initial_header_missing(self):
        # For attributes that can span multiple columns, e.g. note, note_2, note_3
        # if the initial column i.e. 'note' is missing, rest of the columns are ignored

        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_initial_header_missing.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        accepted_columns = validation_report.accepted_columns
        ignored_columns = validation_report.ignored_columns

        assert "note_2" in ignored_columns
        assert "note_3" in ignored_columns

        assert "title" in accepted_columns
        assert "type" in accepted_columns

    def test_base_case_dictionary_entries(self):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_base_case_dictionary_entries.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.new_rows == 2
        assert validation_report.error_rows == 0

    def test_all_non_media_columns_dictionary_entries(self):
        # Testing all non-media columns
        # This test should be updated as new columns are added

        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_all_non_media_columns_dictionary_entries.csv",
            mimetype=self.MIMETYPE,
        )

        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        accepted_columns = validation_report.accepted_columns
        ignored_columns = validation_report.ignored_columns

        assert validation_report.new_rows == 6
        assert validation_report.error_rows == 0

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

    def test_default_values(self):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_default_values.csv",
            mimetype=self.MIMETYPE,
        )

        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.new_rows == 4
        assert validation_report.error_rows == 0

    def test_mix_of_invalid_columns(self):
        # Tests for invalid values present in the following columns
        # type, title, visibility, boolean(include_in_games, include_on_kids_site), part_of_speech

        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_invalid_rows.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)

        validation_report = import_job.validation_report

        error_rows = validation_report.rows.all()
        error_rows_numbers = list(
            validation_report.rows.order_by("row_number").values_list(
                "row_number", flat=True
            )
        )

        assert validation_report.new_rows == 1  # control row
        assert len(error_rows) == 5
        assert error_rows_numbers == [2, 3, 4, 5, 6]

    def test_invalid_categories(self):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_invalid_categories.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        error_rows = validation_report.rows.all()
        error_rows_numbers = list(
            validation_report.rows.values_list("row_number", flat=True)
        )

        assert validation_report.new_rows == 1  # control row
        assert len(error_rows) == 3
        assert error_rows_numbers == [2, 3, 4]

    def test_boolean_variations(self):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_boolean_variations.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.new_rows == 12
        assert validation_report.error_rows == 1

        validation_error_row = validation_report.rows.first()
        assert validation_error_row.row_number == 13
        assert (
            "Invalid value in include_on_kids_site column. Expected 'true' or 'false'."
            in validation_error_row.errors
        )
