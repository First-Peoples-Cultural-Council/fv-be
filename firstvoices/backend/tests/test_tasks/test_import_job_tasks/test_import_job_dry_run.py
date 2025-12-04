from unittest.mock import patch

import pytest
import tablib

from backend.models import ImportJob
from backend.models.constants import Visibility
from backend.models.dictionary import ExternalDictionaryEntrySystem
from backend.models.files import File
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

    def test_mix_of_invalid_rows(self):
        # Tests for invalid values present in the following columns
        # type, title, visibility, boolean(include_in_games, include_on_kids_site), part_of_speech
        # Also verify the CSV generated

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

        # re-opening the file
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_invalid_rows.csv",
            mimetype=self.MIMETYPE,
        )
        input_csv_table = tablib.Dataset().load(
            file_content.read().decode("utf-8-sig"), format="csv"
        )

        failed_rows_csv_table = tablib.Dataset().load(
            import_job.failed_rows_csv.content.read().decode("utf-8-sig"),
            format="csv",
        )

        assert len(failed_rows_csv_table) == 5

        for i in range(0, len(error_rows_numbers)):
            input_index = (
                error_rows_numbers[i] - 1
            )  # since we do +1 while generating error row numbers
            assert input_csv_table[input_index] == failed_rows_csv_table[i]

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

    def test_dry_run_failed(self, caplog):
        # Valid CSV
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_dry_run_failed.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        with patch(
            "backend.tasks.import_job_tasks.process_import_job_data",
            side_effect=Exception("Random exception."),
        ):
            validate_import_job(import_job.id)

            # Refreshed import job instance
            import_job = ImportJob.objects.get(id=import_job.id)
            assert import_job.validation_status == JobStatus.FAILED
            assert "Random exception." in caplog.text

    def test_failed_rows_csv_not_generated_on_valid_rows(self):
        # To verify that failedRowsCsv is not generated if all rows in the input file are valid.

        # Valid CSV
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_failed_rows_csv_not_generated_on_valid_rows.csv",
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
        assert import_job.failed_rows_csv is None

    @pytest.mark.parametrize(
        "validation_status",
        [None, JobStatus.STARTED, JobStatus.COMPLETE, JobStatus.FAILED],
    )
    def test_invalid_validation_status(self, validation_status, caplog):
        # Valid CSV
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_invalid_validation_status.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=validation_status,
        )

        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        assert import_job.validation_status == JobStatus.FAILED
        assert "This job cannot be run due to consistency issues." in caplog.text

    @pytest.mark.parametrize(
        "status", [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE]
    )
    def test_invalid_job_status(self, status, caplog):
        # Valid CSV
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_invalid_job_status.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            status=status,
        )

        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        assert import_job.validation_status == JobStatus.FAILED
        assert (
            "This job could not be started as it is either queued, or already running or completed. "
            f"ImportJob id: {import_job.id}." in caplog.text
        )

    def test_failed_rows_csv_is_updated_or_cleared_after_revalidation(self):
        # If the last validation is successful, the failed rows csv should
        # be updated or deleted
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_failed_rows_csv_invalid_category.csv",
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

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        error_rows_numbers = list(
            validation_report.rows.order_by("row_number").values_list(
                "row_number", flat=True
            )
        )

        assert validation_report.error_rows == 1
        assert error_rows_numbers == [2]
        assert import_job.failed_rows_csv is not None
        failed_rows_csv_id = import_job.failed_rows_csv.id

        # Adding specified invalid_category in the file as a category to the site
        factories.CategoryFactory.create(title="invalid", site=self.site)

        # Validating again
        import_job.validation_status = JobStatus.ACCEPTED
        import_job.save()
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        error_rows_numbers = list(
            validation_report.rows.order_by("row_number").values_list(
                "row_number", flat=True
            )
        )

        assert validation_report.error_rows == 0
        assert error_rows_numbers == []
        assert import_job.failed_rows_csv is None

        import_job_csv = File.objects.filter(id=failed_rows_csv_id)
        assert len(import_job_csv) == 0

    def test_dictionary_entry_external_system_fields(self):
        external_system_1 = ExternalDictionaryEntrySystem(title="Fieldworks")
        external_system_1.save()
        external_system_2 = ExternalDictionaryEntrySystem(title="Dreamworks")
        external_system_2.save()

        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_dictionary_entry_external_system_fields.csv",
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

        assert validation_report.new_rows == 2
        assert validation_report.error_rows == 0

        expected_valid_columns = [
            "title",
            "type",
            "external_system",
            "external_system_entry_id",
        ]

        for column in expected_valid_columns:
            assert column in accepted_columns

        assert len(ignored_columns) == 0
