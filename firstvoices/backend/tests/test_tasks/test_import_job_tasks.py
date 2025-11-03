import uuid
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
import tablib
from django.utils.text import get_valid_filename

from backend.models import DictionaryEntry, ImportJob
from backend.models.constants import Visibility
from backend.models.dictionary import (
    ExternalDictionaryEntrySystem,
    TypeOfDictionaryEntry,
)
from backend.models.files import File
from backend.models.import_jobs import JobStatus
from backend.models.media import ImageFile, VideoFile
from backend.tasks.import_job_tasks import confirm_import_job, validate_import_job
from backend.tests import factories
from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin
from backend.tests.utils import get_sample_file

TEST_AUDIO_IDS = [
    "7763ae50-1b6e-46bc-bd3a-91037ac736cb",
    "addd0095-581f-40b9-afef-fbb394876df7",
]

TEST_DOCUMENT_IDS = [
    "0c0cdd67-2858-4e15-8092-0df9d061e28d",
    "a00d78b1-159b-4c6a-b417-96d4e5819fdd",
]

TEST_IMAGE_IDS = [
    "daf8e74f-f20b-4c81-95c2-7dd744277009",
    "90c561ee-c8ae-4430-b2d2-28bf0c3cf6ff",
]

TEST_VIDEO_IDS = [
    "4764e764-7830-4bea-b30e-4e35cc93b12b",
    "8d998d21-862b-4288-9a3a-ec2fb0a67ad3",
]
VIMEO_VIDEO_LINK = "https://vimeo.com/226053498"
YOUTUBE_VIDEO_LINK = "https://www.youtube.com/watch?v=N_Iyb0LkDUc"


@pytest.mark.django_db
class TestBulkImportDryRun:
    MIMETYPE = "text/csv"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def import_invalid_dictionary_entries(self):
        file_content = get_sample_file(
            "import_job/invalid_dictionary_entries.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)

        return import_job

    def import_minimal_dictionary_entries(self):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)

        return import_job

    def import_batch_with_media_files(self, filename):
        file_content = get_sample_file(f"import_job/{filename}", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-document.pdf", "application/pdf"),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file("sample-image.jpg", "image/jpeg"),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file("video_example_small.mp4", "video/mp4"),
            import_job=import_job,
        )
        return import_job

    def import_with_missing_media(self):
        file_content = get_sample_file("import_job/minimal_media.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)
        validated_import_job = ImportJob.objects.get(id=import_job.id)

        assert validated_import_job.validation_report.error_rows == 4

        return validated_import_job

    def add_missing_media_and_validate(self, import_job):
        # Add the media to the db
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-document.pdf", "application/pdf"),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file("sample-image.jpg", "image/jpeg"),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file("video_example_small.mp4", "video/mp4"),
            import_job=import_job,
        )

        # Validating again
        import_job.validation_status = JobStatus.ACCEPTED
        import_job.save()
        validate_import_job(import_job.id)

    def test_import_task_logs(self, caplog):
        import_job = self.import_minimal_dictionary_entries()

        assert (
            f"Task started. Additional info: ImportJob id: {import_job.id}, dry-run: True."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_base_case_dictionary_entries(self):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.new_rows == 2
        assert validation_report.error_rows == 0

    def test_all_columns_dictionary_entries(self):
        # More columns could be added to this file/test later
        # as we start supporting more columns, e.g. related_media
        file_content = get_sample_file(
            "import_job/all_valid_columns.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
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
        file_content = get_sample_file("import_job/default_values.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.new_rows == 4
        assert validation_report.error_rows == 0

    def test_invalid_rows(self):
        import_job = self.import_invalid_dictionary_entries()
        validation_report = import_job.validation_report

        error_rows = validation_report.rows.all()
        error_rows_numbers = list(
            validation_report.rows.order_by("row_number").values_list(
                "row_number", flat=True
            )
        )

        assert len(error_rows) == 5
        assert error_rows_numbers == [2, 3, 4, 5, 6]

    def test_invalid_categories(self):
        file_content = get_sample_file(
            "import_job/invalid_categories.csv", self.MIMETYPE
        )  # 1st row in the file a valid row for control
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        error_rows = validation_report.rows.all()
        error_rows_numbers = list(
            validation_report.rows.values_list("row_number", flat=True)
        )

        assert len(error_rows) == 3
        assert error_rows_numbers == [3, 4, 5]

    def test_validation_report_columns(self):
        file_content = get_sample_file("import_job/unknown_columns.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        accepted_columns = validation_report.accepted_columns
        ignored_columns = validation_report.ignored_columns

        assert "abc" in ignored_columns
        assert "xyz" in ignored_columns

        assert "title" in accepted_columns
        assert "type" in accepted_columns

    def test_missing_original_column(self):
        file_content = get_sample_file(
            "import_job/original_header_missing.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        accepted_columns = validation_report.accepted_columns
        ignored_columns = validation_report.ignored_columns

        assert "note_2" in ignored_columns
        assert "note_3" in ignored_columns

        assert "title" in accepted_columns
        assert "type" in accepted_columns

    def test_boolean_variations(self):
        file_content = get_sample_file(
            "import_job/boolean_variations.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
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

    def test_related_entries_by_id(self):
        # For entries that are already present in the db
        factories.DictionaryEntryFactory(
            site=self.site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )
        factories.DictionaryEntryFactory(
            site=self.site,
            type=TypeOfDictionaryEntry.PHRASE,
            id=UUID("f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d"),
        )

        file_content = get_sample_file(
            "import_job/related_entries_valid_by_id.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.new_rows == 1
        assert validation_report.error_rows == 0

    def test_invalid_related_entries_by_id(self):
        # For entries that are already present in the db
        # Referring to a different model
        factories.SongFactory(
            site=self.site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )

        file_content = get_sample_file(
            "import_job/related_entries_invalid_by_id.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.new_rows == 0
        assert validation_report.error_rows == 2

        validation_error_rows = validation_report.rows.all().order_by("row_number")

        assert validation_error_rows[0].row_number == 1
        assert (
            "Referenced dictionary entry not found for ID: invalid_uuid"
            in validation_error_rows[0].errors
        )

        assert validation_error_rows[1].row_number == 2
        assert (
            "Referenced dictionary entry not found for ID: 964b2b52-45c3-4c2f-90db-7f34c6599c1c"
            in validation_error_rows[1].errors
        )

    def test_related_entries_by_title(self):
        # For entries from within the same batch import csv file
        file_content = get_sample_file(
            "import_job/related_entries_valid_by_title.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.new_rows == 2
        assert validation_report.error_rows == 0

    def test_related_entry_by_title_invalid_from_entry(self):
        file_content = get_sample_file(
            "import_job/related_entries_invalid_from_entry.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.new_rows == 1
        assert validation_report.error_rows == 1

        error_row = validation_report.rows.first()
        assert error_row.row_number == 1

        expected_error_message = (
            "Entry 'Word 1' was not imported, and could not be linked as a related entry to entry 'Word 2'. "
            "Please link the entries manually after re-importing the missing entry."
        )

        assert error_row.errors[1] == expected_error_message

    def test_related_entry_by_title_invalid_to_entry(self):
        file_content = get_sample_file(
            "import_job/related_entries_invalid_to_entry.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.new_rows == 0
        assert validation_report.error_rows == 2

        error_row = validation_report.rows.get(row_number=1)

        expected_error_message = (
            "Related entry 'Word 2' could not be found to link to entry 'Word 1'. "
            "Please link the entries manually after re-importing the missing entry."
        )

        assert error_row.errors[0] == expected_error_message

    def test_related_entry_by_title_invalid_both_entries(self):
        file_content = get_sample_file(
            "import_job/related_entries_invalid_to_and_from_entry.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.new_rows == 1  # Control row present
        assert validation_report.error_rows == 2

        error_rows = validation_report.rows.all().order_by("row_number")
        error_row_1 = error_rows[0]
        error_row_2 = error_rows[1]

        assert error_row_1.row_number == 1
        assert error_row_2.row_number == 2

        assert len(error_row_1.errors) == 2
        assert (
            "Entry 'Word 1' was not imported, and could not be linked as a related entry to entry 'Word 2'. "
            "Please link the entries manually after re-importing the missing entry."
            in error_row_1.errors[1]
        )

        assert len(error_row_2.errors) == 2
        assert (
            "Entry 'Word 2' was not imported, and could not be linked as a related entry to entry 'Word 1'. "
            "Please link the entries manually after re-importing the missing entry."
            in error_row_2.errors[1]
        )

    def test_related_entries_duplicate_titles_same_row(self):
        # if a related entry title appears in the same row multiple times, fail the row
        file_content = get_sample_file(
            "import_job/related_entries_duplicate_titles_same_row.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        # Updated instance
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.new_rows == 1
        assert validation_report.error_rows == 1

        error_row = validation_report.rows.first()
        assert error_row.row_number == 1
        assert (
            "Duplicate related entry title 'Word 2' found in column 'related_entry_2'. "
            "Please ensure each related entry title is unique per entry."
        )

    def test_dry_run_failed(self, caplog):
        file = factories.FileFactory(
            content=get_sample_file("import_job/all_valid_columns.csv", self.MIMETYPE)
        )

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

            # Updated import job instance
            import_job = ImportJob.objects.get(id=import_job.id)
            assert import_job.validation_status == JobStatus.FAILED
            assert "Random exception." in caplog.text

    def test_failed_rows_csv(self):
        import_job = self.import_invalid_dictionary_entries()
        validation_report = import_job.validation_report
        error_rows = validation_report.rows.all()
        error_rows_numbers = list(
            validation_report.rows.order_by("row_number").values_list(
                "row_number", flat=True
            )
        )
        assert len(error_rows) == 5
        assert error_rows_numbers == [2, 3, 4, 5, 6]

        # Reading actual file
        file_content = get_sample_file(
            "import_job/invalid_dictionary_entries.csv", self.MIMETYPE
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

    def test_failed_rows_csv_not_generated_on_valid_rows(self):
        # To verify no failedRowsCsv is generated if all rows
        # in the input file are valid.

        import_job = self.import_minimal_dictionary_entries()
        assert import_job.failed_rows_csv is None

    @pytest.mark.parametrize(
        "validation_status",
        [None, JobStatus.STARTED, JobStatus.COMPLETE, JobStatus.FAILED],
    )
    def test_invalid_validation_status(self, validation_status, caplog):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=validation_status,
        )

        validate_import_job(import_job.id)
        import_job = ImportJob.objects.filter(id=import_job.id)[0]
        assert import_job.validation_status == JobStatus.FAILED
        assert "This job cannot be run due to consistency issues." in caplog.text

    @pytest.mark.parametrize(
        "status", [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE]
    )
    def test_invalid_job_status(self, status, caplog):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            status=status,
        )

        validate_import_job(import_job.id)
        import_job = ImportJob.objects.filter(id=import_job.id)[0]
        assert import_job.validation_status == JobStatus.FAILED
        assert (
            "This job could not be started as it is either queued, or already running or completed. "
            f"ImportJob id: {import_job.id}." in caplog.text
        )

    def test_failed_rows_csv_is_updated_or_cleared_after_revalidation(self):
        # If the last validation is successful, the failed rows csv should
        # be updated or deleted
        file_content = get_sample_file("import_job/invalid_m2m.csv", self.MIMETYPE)
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

        # Adding invalid_category as a category to the site
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

    def test_missing_media(self):
        import_job = self.import_with_missing_media()
        error_rows = import_job.validation_report.rows.all().order_by("row_number")
        error_rows_numbers = error_rows.values_list("row_number", flat=True)

        assert list(error_rows_numbers) == [1, 2, 3, 4]

        assert (
            "Media file missing in uploaded files: sample-audio.mp3, column: audio_filename."
            in error_rows[0].errors
        )
        assert (
            "Media file missing in uploaded files: sample-image.jpg, column: img_filename."
            in error_rows[1].errors
        )
        assert (
            "Media file missing in uploaded files: video_example_small.mp4, column: video_filename."
            in error_rows[2].errors
        )
        assert (
            "Media file missing in uploaded files: sample-document.pdf, column: document_filename."
            in error_rows[3].errors
        )

    def test_all_media_present(self):
        # Start with a validated import job that has missing media
        import_job = self.import_with_missing_media()

        self.add_missing_media_and_validate(import_job)

        # Verifying all missing media errors are resolved now
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0
        assert validation_report.rows.count() == 0

    def test_failed_rows_csv_deleted(self):
        # Start with a validated import job that has missing media
        import_job = self.import_with_missing_media()
        failed_rows_csv_id = import_job.failed_rows_csv.id

        self.add_missing_media_and_validate(import_job)

        import_job_csv = File.objects.filter(id=failed_rows_csv_id)
        assert len(import_job_csv) == 0

    def test_failed_rows_csv_deleted_and_replaced(self):
        # Start with a validated import job that has missing media
        import_job = self.import_with_missing_media()
        first_failed_rows_csv_id = import_job.failed_rows_csv.id

        # Add some of the media to the db
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-document.pdf", "application/pdf"),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file("sample-image.jpg", "image/jpeg"),
            import_job=import_job,
        )

        # Validating again
        import_job.validation_status = JobStatus.ACCEPTED
        import_job.save()
        validate_import_job(import_job.id)

        revalidated_import_job = ImportJob.objects.get(id=import_job.id)

        # Check that the out of date csv has been deleted
        first_failed_rows_csv = File.objects.filter(
            site=self.site, id=first_failed_rows_csv_id
        )
        assert len(first_failed_rows_csv) == 0

        # Confirm there is a new csv
        assert first_failed_rows_csv_id != revalidated_import_job.failed_rows_csv.id
        assert revalidated_import_job.failed_rows_csv is not None
        validation_report = revalidated_import_job.validation_report
        assert validation_report.error_rows == 1

    def test_related_audio_speakers(self):
        file_content = get_sample_file("import_job/related_audio.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("import_job/Another audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 1
        assert (
            "No Person found with the provided name in column audio_speaker."
            in validation_report.rows.all()[0].errors
        )

        factories.PersonFactory.create(name="Test Speaker 1", site=self.site)
        factories.PersonFactory.create(name="Test Speaker 2", site=self.site)

        import_job.validation_status = JobStatus.ACCEPTED
        import_job.save()
        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0

    def test_multiple_errors_in_single_row(self):
        # If there are multiple issues present in one row, all issues should be displayed
        # along with their column name
        import_job = self.import_batch_with_media_files("mixed_errors.csv")
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 1

        error_row = validation_report.rows.get(row_number=1)
        assert len(error_row.errors) == 4
        assert (
            "Invalid value in include_in_games column. Expected 'true' or 'false'."
            in error_row.errors
        )
        assert (
            "No Person found with the provided name in column audio_speaker."
            in error_row.errors
        )
        assert (
            "Invalid value in img_include_in_kids_site column. Expected 'true' or 'false'."
            in error_row.errors
        )
        assert (
            "Invalid value in video_include_in_kids_site column. Expected 'true' or 'false'."
            in error_row.errors
        )

    def test_duplicate_media_filenames(self):
        # If multiple rows have same filenames, only the first media instance will be imported
        # and used. The rest of the media will not be imported and should not give any issues.
        import_job = self.import_batch_with_media_files("duplicate_media_filenames.csv")
        factories.PersonFactory.create(name="Test Speaker 1", site=self.site)
        factories.PersonFactory.create(name="Test Speaker 2", site=self.site)

        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0

    def test_related_media_id_columns_accepted(self):
        file_content = get_sample_file(
            "import_job/minimal_media_ids.csv", self.MIMETYPE
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
        assert "audio_ids" in validation_report.accepted_columns
        assert "document_ids" in validation_report.accepted_columns
        assert "img_ids" in validation_report.accepted_columns
        assert "video_ids" in validation_report.accepted_columns

    def test_related_media_id_and_filename_columns_accepted(self):
        file_content = get_sample_file(
            "import_job/minimal_media_mixed.csv", self.MIMETYPE
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
        assert "audio_ids" in validation_report.accepted_columns
        assert "audio_filename" in validation_report.accepted_columns
        assert "document_ids" in validation_report.accepted_columns
        assert "document_filename" in validation_report.accepted_columns
        assert "img_ids" in validation_report.accepted_columns
        assert "img_filename" in validation_report.accepted_columns
        assert "video_ids" in validation_report.accepted_columns
        assert "video_filename" in validation_report.accepted_columns

    def test_related_media_id_does_not_exist(self):
        file_content = get_sample_file(
            "import_job/minimal_media_ids.csv", self.MIMETYPE
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
        assert validation_report.error_rows == 5

    def test_related_media_id_wrong_site(self):
        factories.AudioFactory.create()
        factories.DocumentFactory.create()
        factories.ImageFactory.create()
        factories.VideoFactory.create()

        file_content = get_sample_file(
            "import_job/minimal_media_ids.csv", self.MIMETYPE
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
        assert validation_report.error_rows == 5

    def test_related_media_id_wrong_type(self):
        factories.AudioFactory.create(site=self.site, id=TEST_VIDEO_IDS[0])  # video_id
        factories.DocumentFactory.create(
            site=self.site, id=TEST_IMAGE_IDS[0]
        )  # image_id
        factories.ImageFactory.create(site=self.site, id=TEST_AUDIO_IDS[0])  # audio_id
        factories.VideoFactory.create(site=self.site, id=TEST_IMAGE_IDS[0])  # image_id

        file_content = get_sample_file(
            "import_job/minimal_media_ids.csv", self.MIMETYPE
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
        assert validation_report.error_rows == 5

    def test_related_media_id_success_same_site(self):
        audio = factories.AudioFactory.create(id=TEST_AUDIO_IDS[0])
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=audio.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=audio.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=audio.site)

        file_content = get_sample_file(
            "import_job/minimal_media_ids.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=audio.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 5

    def test_related_media_id_success_shared_site(self):
        audio = factories.AudioFactory.create(id=TEST_AUDIO_IDS[0])
        factories.SiteFeatureFactory.create(
            site=audio.site, key="shared_media", is_enabled=True
        )

        document = factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0])
        factories.SiteFeatureFactory.create(
            site=document.site, key="SHARED_MEDIA", is_enabled=True
        )

        image = factories.ImageFactory.create(id=TEST_IMAGE_IDS[0])
        factories.SiteFeatureFactory.create(
            site=image.site, key="shared_media", is_enabled=True
        )

        video = factories.VideoFactory.create(id=TEST_VIDEO_IDS[0])
        factories.SiteFeatureFactory.create(
            site=video.site, key="SHARED_MEDIA", is_enabled=True
        )

        file_content = get_sample_file(
            "import_job/minimal_media_ids.csv", self.MIMETYPE
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
        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 5

    def test_related_media_id_failed_shared_site(self):
        audio = factories.AudioFactory.create(id=TEST_AUDIO_IDS[0])
        factories.SiteFeatureFactory.create(
            site=audio.site, key="shared_media", is_enabled=False
        )

        document = factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0])
        factories.SiteFeatureFactory.create(
            site=document.site, key="shared_media", is_enabled=False
        )

        image = factories.ImageFactory.create(id=TEST_IMAGE_IDS[0])
        factories.SiteFeatureFactory.create(
            site=image.site, key="shared_media", is_enabled=False
        )

        video = factories.VideoFactory.create(id=TEST_VIDEO_IDS[0])
        factories.SiteFeatureFactory.create(
            site=video.site, key="NOT_SHARED_MEDIA", is_enabled=True
        )

        file_content = get_sample_file(
            "import_job/minimal_media_ids.csv", self.MIMETYPE
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
        assert validation_report.error_rows == 5

    def test_dictionary_entry_external_system_fields(self):
        external_system_1 = ExternalDictionaryEntrySystem(title="Fieldworks")
        external_system_1.save()
        external_system_2 = ExternalDictionaryEntrySystem(title="Dreamworks")
        external_system_2.save()

        file_content = get_sample_file(
            "import_job/dictionary_entry_external_system_fields.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)
        # Updated instance
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

    def test_related_media_id_duplicate_ids(self):
        audio = factories.AudioFactory.create(id=TEST_AUDIO_IDS[0])
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=audio.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=audio.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=audio.site)

        file_content = get_sample_file(
            "import_job/related_media_ids_multiple_duplicate.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=audio.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 5

    def test_related_media_id_mixed_invalid_and_valid(self):
        audio = factories.AudioFactory.create(id=TEST_AUDIO_IDS[0])
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=audio.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=audio.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=audio.site)

        file_content = get_sample_file(
            "import_job/related_media_ids_multiple.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=audio.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 5
        assert validation_report.new_rows == 0

    def test_missing_media_multiple(self):
        import_job = self.import_batch_with_media_files("missing_media_multiple.csv")
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 4

        error_rows = validation_report.rows.all().order_by("row_number")
        assert (
            "Media file missing in uploaded files: missing-audio.mp3, column: audio_2_filename."
            in error_rows[0].errors
        )
        assert (
            "Media file missing in uploaded files: missing-image.jpg, column: img_2_filename."
            in error_rows[1].errors
        )
        assert (
            "Media file missing in uploaded files: missing-video.mp4, column: video_2_filename."
            in error_rows[2].errors
        )
        assert (
            "Media file missing in uploaded files: missing-document.pdf, column: document_2_filename."
            in error_rows[3].errors
        )

    def test_invalid_video_embed_links(self):
        file_content = get_sample_file(
            "import_job/invalid_video_embed_links.csv", self.MIMETYPE
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

        assert validation_report.new_rows == 0
        assert validation_report.error_rows == 3

        error_rows = validation_report.rows.all().order_by("row_number")
        assert (
            "related_video_links: Item 1 in the array did not validate: Enter a valid URL."
            in error_rows[0].errors
        )
        assert (
            "related_video_links: Duplicate urls found in list." in error_rows[1].errors
        )
        assert (
            "related_video_links: Duplicate urls found in list." in error_rows[2].errors
        )


@pytest.mark.django_db
class TestBulkImport(IgnoreTaskResultsMixin):
    MIMETYPE = "text/csv"
    TASK = confirm_import_job

    ACKNOWLEDGEMENT = "Test Ack"
    AUDIO_TITLE = "Related Audio"
    AUDIO_DESCRIPTION = "Testing audio upload"
    DOCUMENT_TITLE = "Related Document"
    DOCUMENT_DESCRIPTION = "Testing document upload"
    IMAGE_TITLE = "Related Image"
    IMAGE_DESCRIPTION = "Testing image upload"
    TEST_SPEAKER = "Test Speaker"
    VIDEO_TITLE = "Related Video"
    VIDEO_DESCRIPTION = "Testing video upload"

    def get_valid_task_args(self):
        return (uuid.uuid4(),)

    def setup_method(self):
        self.user = factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def confirm_upload_with_media_files(self, filename):
        file_content = get_sample_file(f"import_job/{filename}", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        factories.PersonFactory.create(name=f"{self.TEST_SPEAKER} 1", site=self.site)
        factories.PersonFactory.create(name=f"{self.TEST_SPEAKER} 2", site=self.site)
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("import_job/Another audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-document.pdf", "application/pdf"),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                "import_job/Another document.pdf", "application/pdf"
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file("sample-image.jpg", "audio/mpeg"),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file("import_job/Another image.jpg", "audio/mpeg"),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file("video_example_small.mp4", "video/mp4"),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file("import_job/Another video.mp4", "video/mp4"),
            import_job=import_job,
        )

        confirm_import_job(import_job.id)
        return import_job

    def upload_multiple_media_files(self, count, filename, file_type, import_job):
        if file_type == "audio":
            base_file = "sample-audio.mp3"
            file_ext = ".mp3"
            media_factory = factories.FileFactory
            mimetype = "audio/mpeg"
        elif file_type == "image":
            base_file = "sample-image.jpg"
            file_ext = ".jpg"
            media_factory = factories.ImageFileFactory
            mimetype = "image/jpeg"
        elif file_type == "video":
            base_file = "video_example_small.mp4"
            file_ext = ".mp4"
            media_factory = factories.VideoFileFactory
            mimetype = "video/mp4"
        elif file_type == "document":
            base_file = "sample-document.pdf"
            file_ext = ".pdf"
            media_factory = factories.FileFactory
            mimetype = "application/pdf"
        else:
            return

        for x in range(1, count + 1):
            media_factory(
                site=self.site,
                content=get_sample_file(
                    filename=f"{base_file}",
                    mimetype=mimetype,
                    title=f"{filename}-{x}{file_ext}",
                ),
                import_job=import_job,
            )

    def assert_related_media_details(self, related_media, suffix_number=""):
        assert related_media.acknowledgement == f"{self.ACKNOWLEDGEMENT}{suffix_number}"
        assert related_media.exclude_from_kids is False

    def assert_related_audio_details(self, filename, related_audio, suffix_number=""):
        assert f"{filename}{suffix_number}.mp3" in related_audio.original.content.name
        assert related_audio.title == f"{self.AUDIO_TITLE}{suffix_number}"
        assert related_audio.description == f"{self.AUDIO_DESCRIPTION}{suffix_number}"
        assert related_audio.exclude_from_games is True
        self.assert_related_media_details(related_audio, suffix_number)

    def assert_related_document_details(
        self, filename, related_document, suffix_number=""
    ):
        assert (
            f"{filename}{suffix_number}.pdf" in related_document.original.content.name
        )
        assert related_document.title == f"{self.DOCUMENT_TITLE}{suffix_number}"
        assert (
            related_document.description
            == f"{self.DOCUMENT_DESCRIPTION}{suffix_number}"
        )
        assert related_document.exclude_from_games is False
        self.assert_related_media_details(related_document, suffix_number)

    def assert_related_image_details(self, filename, related_image, suffix_number=""):
        assert f"{filename}{suffix_number}.jpg" in related_image.original.content.name
        assert related_image.title == f"{self.IMAGE_TITLE}{suffix_number}"
        assert related_image.description == f"{self.IMAGE_DESCRIPTION}{suffix_number}"
        assert related_image.exclude_from_games is False
        self.assert_related_media_details(related_image, suffix_number)

    def assert_related_video_details(self, filename, related_video, suffix_number=""):
        assert f"{filename}{suffix_number}.mp4" in related_video.original.content.name
        assert related_video.title == f"{self.VIDEO_TITLE}{suffix_number}"
        assert related_video.description == f"{self.VIDEO_DESCRIPTION}{suffix_number}"
        assert related_video.exclude_from_games is False
        self.assert_related_media_details(related_video, suffix_number)

    def assert_max_speakers(self, related_audio, suffix_number):
        assert related_audio.speakers.count() == 5
        expected_speakers = [
            f"{self.TEST_SPEAKER} {suffix_number}-{i}" for i in range(1, 6)
        ]
        actual_speakers = list(related_audio.speakers.values_list("name", flat=True))
        assert all(speaker in actual_speakers for speaker in expected_speakers)

    def test_import_task_logs(self, caplog):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert (
            f"Task started. Additional info: ImportJob id: {import_job.id}, dry-run: False."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_base_case_dictionary_entries(self):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        # word
        word = DictionaryEntry.objects.filter(title="abc")[0]
        assert word.type == TypeOfDictionaryEntry.WORD
        assert word.created_by == self.user
        assert word.last_modified_by == self.user
        assert word.system_last_modified >= word.last_modified
        assert word.system_last_modified_by == import_job.created_by
        # phrase
        phrase = DictionaryEntry.objects.filter(title="xyz")[0]
        assert phrase.type == TypeOfDictionaryEntry.PHRASE
        assert phrase.created_by == self.user
        assert phrase.last_modified_by == self.user
        assert phrase.system_last_modified >= phrase.last_modified
        assert phrase.system_last_modified_by == import_job.created_by

    def test_all_columns_dictionary_entries(self):
        file_content = get_sample_file(
            "import_job/all_valid_columns.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        # Verifying first entry
        first_entry = DictionaryEntry.objects.filter(title="Word 1")[0]
        assert first_entry.type == TypeOfDictionaryEntry.WORD
        assert first_entry.visibility == Visibility.PUBLIC
        assert first_entry.part_of_speech.title == "Adjective"
        assert first_entry.exclude_from_games is False
        assert first_entry.exclude_from_kids is True
        assert first_entry.translations == [
            "first_translation",
            "second_translation",
            "third_translation",
            "fourth_translation",
            "fifth_translation",
        ]
        assert first_entry.acknowledgements == [
            "first_ack",
            "second_ack",
            "third_ack",
            "fourth_ack",
            "fifth_ack",
        ]
        assert first_entry.notes == [
            "first_note",
            "second_note",
            "third_note",
            "fourth_note",
            "fifth_note",
        ]
        assert first_entry.alternate_spellings == [
            "alt_s_1",
            "alt_s_2",
            "alt_s_3",
            "alt_s_4",
            "alt_s_5",
        ]
        assert first_entry.pronunciations == [
            "first_p",
            "second_p",
            "third_p",
            "fourth_p",
            "fifth_p",
        ]

        categories = list(first_entry.categories.all().values_list("title", flat=True))
        assert "Animals" in categories
        assert "Body" in categories

    def test_default_values(self):
        file_content = get_sample_file("import_job/default_values.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )
        confirm_import_job(import_job.id)

        # Verifying default type
        empty_type = DictionaryEntry.objects.filter(title="Empty type")[0]
        assert empty_type.type == TypeOfDictionaryEntry.WORD

        # default visibility
        empty_visibility = DictionaryEntry.objects.filter(title="Empty visibility")[0]
        assert empty_visibility.visibility == Visibility.TEAM

        # default audience flags
        empty_games_flag = DictionaryEntry.objects.filter(
            title="Empty include in games"
        )[0]
        assert empty_games_flag.exclude_from_games is False
        empty_kids_flag = DictionaryEntry.objects.filter(
            title="Empty include on kids site"
        )[0]
        assert empty_kids_flag.exclude_from_kids is False

    def test_import_job_failed(self, caplog):
        file = factories.FileFactory(
            content=get_sample_file("import_job/all_valid_columns.csv", self.MIMETYPE)
        )

        # Mock that the task has already completed
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        with patch(
            "backend.tasks.import_job_tasks.process_import_job_data",
            side_effect=Exception("Random exception."),
        ):
            confirm_import_job(import_job.id)

            # Updated import job instance
            import_job = ImportJob.objects.get(id=import_job.id)
            assert import_job.status == JobStatus.FAILED
            assert "Random exception." in caplog.text

    def test_multiple_related_entries_by_id(self):
        # For entries that are already present in the db
        existing_entry1 = factories.DictionaryEntryFactory.create(
            site=self.site, id="964b2b52-45c3-4c2f-90db-7f34c6599c1c"
        )
        existing_entry2 = factories.DictionaryEntryFactory.create(
            site=self.site, id="f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d"
        )

        file_content = get_sample_file(
            "import_job/related_entries_valid_by_id.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 3

        new_entry = DictionaryEntry.objects.get(title="Word 1")
        related_entry_list = [
            str(value)
            for value in new_entry.dictionaryentrylink_set.values_list(
                "to_dictionary_entry_id", flat=True
            )
        ]

        assert len(related_entry_list) == 2
        assert existing_entry1.id in related_entry_list
        assert existing_entry2.id in related_entry_list

    def test_related_entry_import_by_title(self):
        file_content = get_sample_file(
            "import_job/related_entries_valid_by_title.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 2

        entry1 = DictionaryEntry.objects.get(title="Word 1")
        related_entry1 = entry1.dictionaryentrylink_set.first()
        assert related_entry1.to_dictionary_entry.title == "Word 2"

        entry2 = DictionaryEntry.objects.get(title="Word 2")
        related_entry2 = entry2.dictionaryentrylink_set.first()
        assert related_entry2.to_dictionary_entry.title == "Word 1"

    def test_related_entries_import_by_title_full(self):
        file_content = get_sample_file(
            "import_job/related_entries_valid_by_title_full.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 6

        entry1 = DictionaryEntry.objects.get(title="Word 1")
        related_entries = entry1.dictionaryentrylink_set.all()
        assert related_entries.count() == 5

        expected_related_titles = [
            "Word 2",
            "Word 3",
            "Phrase 1",
            "Phrase 2",
            "Phrase 3",
        ]
        actual_related_titles = [
            related_entry.to_dictionary_entry.title for related_entry in related_entries
        ]
        assert all(title in actual_related_titles for title in expected_related_titles)

    def test_related_entry_import_missing_to_entry(self):
        file_content = get_sample_file(
            "import_job/related_entries_invalid_to_entry.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 0

    def test_related_entries_duplicate_titles(self):
        # If there are multiple entries with the same title, only link the first instance of that title
        file_content = get_sample_file(
            "import_job/related_entries_duplicate_titles.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 3

        entry1 = DictionaryEntry.objects.get(title="Word 1")
        related_entries = entry1.dictionaryentrylink_set.all()
        assert related_entries.count() == 1
        assert related_entries[0].to_dictionary_entry.title == "Word 2"
        assert related_entries[0].to_dictionary_entry.notes[0] == "first instance"

    def test_related_entries_duplicate_titles_same_row(self):
        # Ensure no duplicate links are created if the same title is in the same row multiple times
        file_content = get_sample_file(
            "import_job/related_entries_duplicate_titles_same_row.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 1

    def test_related_entries_cannot_link_to_self(self):
        # Ensure no links are created to self
        file_content = get_sample_file(
            "import_job/related_entries_self_link.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 1

        entry1 = DictionaryEntry.objects.get(title="Word 1")
        related_entries = entry1.dictionaryentrylink_set.all()
        assert related_entries.count() == 0

    def test_skip_rows_with_erroneous_values(self):
        # If a row has validation errors, skip that row, but import the rest of the file
        file_content = get_sample_file(
            "import_job/invalid_dictionary_entries.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
        )
        confirm_import_job(import_job.id)

        imported_entries = DictionaryEntry.objects.all()
        assert len(imported_entries) == 1
        assert imported_entries[0].title == "Phrase 1"

    def test_invalid_m2m_entries_not_imported(self):
        # Testing out with categories, but is similar
        # for any m2m relation.

        file_content = get_sample_file(
            "import_job/invalid_m2m.csv", self.MIMETYPE
        )  # 1st row in the file a valid row for control
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        dictionary_entries_count = DictionaryEntry.objects.all().count()
        assert dictionary_entries_count == 1
        assert DictionaryEntry.objects.first().title == "Valid m2m"

    def test_import_id_added_to_imported_entries(self):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        # word
        word = DictionaryEntry.objects.filter(title="abc")[0]
        assert word.import_job == import_job

        # phrase
        phrase = DictionaryEntry.objects.filter(title="xyz")[0]
        assert phrase.import_job == import_job

    @pytest.mark.parametrize(
        "status", [None, JobStatus.STARTED, JobStatus.COMPLETE, JobStatus.FAILED]
    )
    def test_invalid_status(self, status, caplog):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site, run_as_user=self.user, data=file, status=status
        )

        confirm_import_job(import_job.id)
        import_job = ImportJob.objects.filter(id=import_job.id)[0]
        assert import_job.validation_status == JobStatus.FAILED
        assert (
            f"This job cannot be run due to consistency issues. ImportJob id: {import_job.id}."
            in caplog.text
        )

    @pytest.mark.parametrize(
        "validation_status",
        [None, JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.FAILED],
    )
    def test_invalid_validation_status(self, validation_status, caplog):
        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            status=JobStatus.ACCEPTED,
            validation_status=validation_status,
        )

        confirm_import_job(import_job.id)
        import_job = ImportJob.objects.filter(id=import_job.id)[0]
        assert import_job.validation_status == JobStatus.FAILED
        assert (
            f"Please validate the job before confirming the import. ImportJob id: {import_job.id}."
            in caplog.text
        )

    def test_related_audio(self):
        import_job = self.confirm_upload_with_media_files("related_audio.csv")

        entry_with_audio = DictionaryEntry.objects.get(title="Word 1")
        related_audio = entry_with_audio.related_audio.all()
        assert len(related_audio) == 1

        related_audio = related_audio[0]
        self.assert_related_audio_details("sample-audio", related_audio)
        assert related_audio.system_last_modified >= related_audio.last_modified
        assert related_audio.system_last_modified_by == import_job.created_by

        entry_2 = DictionaryEntry.objects.get(title="Word 2")
        related_audio = entry_2.related_audio.all()
        assert len(related_audio) == 1
        related_audio = related_audio[0]
        assert (
            get_valid_filename("Another audio") in related_audio.original.content.name
        )

    def test_related_audio_multiple_files(self):
        file_content = get_sample_file(
            "import_job/related_audio_multiple.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        self.upload_multiple_media_files(6, "related_audio", "audio", import_job)
        factories.PersonFactory.create(name=f"{self.TEST_SPEAKER} 1-1", site=self.site)
        factories.PersonFactory.create(name=f"{self.TEST_SPEAKER} 1-2", site=self.site)
        factories.PersonFactory.create(name=f"{self.TEST_SPEAKER} 2-1", site=self.site)
        factories.PersonFactory.create(name=f"{self.TEST_SPEAKER} 2-2", site=self.site)

        confirm_import_job(import_job.id)

        entry_1 = DictionaryEntry.objects.get(title="Word 1")
        related_audio_1 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-1")
        self.assert_related_audio_details("related_audio", related_audio_1, "-1")
        related_audio_1_speakers = list(
            related_audio_1.speakers.all().values_list("name", flat=True)
        )
        assert f"{self.TEST_SPEAKER} 1-1" in related_audio_1_speakers
        assert f"{self.TEST_SPEAKER} 1-2" in related_audio_1_speakers

        related_audio_2 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-2")
        self.assert_related_audio_details("related_audio", related_audio_2, "-2")
        related_audio_2_speakers = list(
            related_audio_2.speakers.all().values_list("name", flat=True)
        )
        assert f"{self.TEST_SPEAKER} 2-1" in related_audio_2_speakers
        assert f"{self.TEST_SPEAKER} 2-2" in related_audio_2_speakers

        entry_2 = DictionaryEntry.objects.get(title="Word 2")
        related_audio_3 = entry_2.related_audio.get(title=f"{self.AUDIO_TITLE}-3")
        self.assert_related_audio_details("related_audio", related_audio_3, "-3")
        related_audio_4 = entry_2.related_audio.get(title=f"{self.AUDIO_TITLE}-4")
        self.assert_related_audio_details("related_audio", related_audio_4, "-4")

        entry_3 = DictionaryEntry.objects.get(title="Word 3")
        related_audio_5 = entry_3.related_audio.get(title=f"{self.AUDIO_TITLE}-5")
        self.assert_related_audio_details("related_audio", related_audio_5, "-5")
        related_audio_6 = entry_3.related_audio.get(title=f"{self.AUDIO_TITLE}-6")
        self.assert_related_audio_details("related_audio", related_audio_6, "-6")

    def test_related_documents(self):
        import_job = self.confirm_upload_with_media_files("related_documents.csv")

        entry_with_document = DictionaryEntry.objects.filter(title="Word 1")[0]
        related_documents = entry_with_document.related_documents.all()
        assert len(related_documents) == 1

        related_document = related_documents[0]
        self.assert_related_document_details("sample-document", related_document)
        assert related_document.system_last_modified >= related_document.last_modified
        assert related_document.system_last_modified_by == import_job.created_by

        entry_2 = DictionaryEntry.objects.get(title="Word 2")
        related_documents = entry_2.related_documents.all()
        assert len(related_documents) == 1
        related_document = related_documents[0]
        assert (
            get_valid_filename("Another document")
            in related_document.original.content.name
        )

    def test_related_documents_multiple_files(self):
        file_content = get_sample_file(
            "import_job/related_documents_multiple.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        self.upload_multiple_media_files(6, "related_document", "document", import_job)
        confirm_import_job(import_job.id)

        entry_1 = DictionaryEntry.objects.get(title="Word 1")
        related_document_1 = entry_1.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-1"
        )
        self.assert_related_document_details(
            "related_document", related_document_1, "-1"
        )
        related_document_2 = entry_1.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-2"
        )
        self.assert_related_document_details(
            "related_document", related_document_2, "-2"
        )

        entry_2 = DictionaryEntry.objects.get(title="Word 2")
        related_document_3 = entry_2.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-3"
        )
        self.assert_related_document_details(
            "related_document", related_document_3, "-3"
        )
        related_document_4 = entry_2.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-4"
        )
        self.assert_related_document_details(
            "related_document", related_document_4, "-4"
        )

        entry_3 = DictionaryEntry.objects.get(title="Word 3")
        related_document_5 = entry_3.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-5"
        )
        self.assert_related_document_details(
            "related_document", related_document_5, "-5"
        )
        related_document_6 = entry_3.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-6"
        )
        self.assert_related_document_details(
            "related_document", related_document_6, "-6"
        )

    def test_related_images(self):
        import_job = self.confirm_upload_with_media_files("related_images.csv")

        entry_with_image = DictionaryEntry.objects.filter(title="Word 1")[0]
        related_images = entry_with_image.related_images.all()
        assert len(related_images) == 1

        related_image = related_images[0]
        self.assert_related_image_details("sample-image", related_image)
        assert related_image.system_last_modified >= related_image.last_modified
        assert related_image.system_last_modified_by == import_job.created_by

        entry_2 = DictionaryEntry.objects.get(title="Word 2")
        related_images = entry_2.related_images.all()
        assert len(related_images) == 1
        related_image = related_images[0]
        assert (
            get_valid_filename("Another image") in related_image.original.content.name
        )

    def test_related_images_multiple_files(self):
        file_content = get_sample_file(
            "import_job/related_images_multiple.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        self.upload_multiple_media_files(6, "related_image", "image", import_job)
        confirm_import_job(import_job.id)

        entry_1 = DictionaryEntry.objects.get(title="Word 1")
        related_image_1 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-1")
        self.assert_related_image_details("related_image", related_image_1, "-1")
        related_image_2 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-2")
        self.assert_related_image_details("related_image", related_image_2, "-2")

        entry_2 = DictionaryEntry.objects.get(title="Word 2")
        related_image_3 = entry_2.related_images.get(title=f"{self.IMAGE_TITLE}-3")
        self.assert_related_image_details("related_image", related_image_3, "-3")
        related_image_4 = entry_2.related_images.get(title=f"{self.IMAGE_TITLE}-4")
        self.assert_related_image_details("related_image", related_image_4, "-4")

        entry_3 = DictionaryEntry.objects.get(title="Word 3")
        related_image_5 = entry_3.related_images.get(title=f"{self.IMAGE_TITLE}-5")
        self.assert_related_image_details("related_image", related_image_5, "-5")
        related_image_6 = entry_3.related_images.get(title=f"{self.IMAGE_TITLE}-6")
        self.assert_related_image_details("related_image", related_image_6, "-6")

    def test_related_videos(self):
        import_job = self.confirm_upload_with_media_files("related_videos.csv")

        entry_with_video = DictionaryEntry.objects.filter(title="Word 1")[0]
        related_videos = entry_with_video.related_videos.all()
        assert len(related_videos) == 1

        related_video = related_videos[0]
        self.assert_related_video_details("video_example_small", related_video)
        assert related_video.system_last_modified >= related_video.last_modified
        assert related_video.system_last_modified_by == import_job.created_by

        entry_2 = DictionaryEntry.objects.get(title="Word 2")
        related_videos = entry_2.related_videos.all()
        assert len(related_videos) == 1
        related_video = related_videos[0]
        assert (
            get_valid_filename("Another video") in related_video.original.content.name
        )

    def test_related_videos_multiple_files(self):
        file_content = get_sample_file(
            "import_job/related_videos_multiple.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        self.upload_multiple_media_files(6, "related_video", "video", import_job)
        confirm_import_job(import_job.id)

        entry_1 = DictionaryEntry.objects.get(title="Word 1")
        related_video_1 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-1")
        self.assert_related_video_details("related_video", related_video_1, "-1")
        related_video_2 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-2")
        self.assert_related_video_details("related_video", related_video_2, "-2")

        entry_2 = DictionaryEntry.objects.get(title="Word 2")
        related_video_3 = entry_2.related_videos.get(title=f"{self.VIDEO_TITLE}-3")
        self.assert_related_video_details("related_video", related_video_3, "-3")
        related_video_4 = entry_2.related_videos.get(title=f"{self.VIDEO_TITLE}-4")
        self.assert_related_video_details("related_video", related_video_4, "-4")

        entry_3 = DictionaryEntry.objects.get(title="Word 3")
        related_video_5 = entry_3.related_videos.get(title=f"{self.VIDEO_TITLE}-5")
        self.assert_related_video_details("related_video", related_video_5, "-5")
        related_video_6 = entry_3.related_videos.get(title=f"{self.VIDEO_TITLE}-6")
        self.assert_related_video_details("related_video", related_video_6, "-6")

    def test_related_media_full(self):
        file_content = get_sample_file(
            "import_job/related_media_full.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        self.upload_multiple_media_files(5, "related_audio", "audio", import_job)
        self.upload_multiple_media_files(5, "related_image", "image", import_job)
        self.upload_multiple_media_files(5, "related_video", "video", import_job)
        self.upload_multiple_media_files(5, "related_document", "document", import_job)

        for x in range(1, 6):
            for z in range(1, 6):
                factories.PersonFactory.create(
                    name=f"Test Speaker {x}-{z}", site=self.site
                )

        confirm_import_job(import_job.id)

        entry_1 = DictionaryEntry.objects.get(title="Word 1")
        related_audio_1 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-1")
        self.assert_related_audio_details("related_audio", related_audio_1, "-1")
        self.assert_max_speakers(related_audio_1, "1")
        related_audio_2 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-2")
        self.assert_related_audio_details("related_audio", related_audio_2, "-2")
        self.assert_max_speakers(related_audio_2, "2")
        related_audio_3 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-3")
        self.assert_related_audio_details("related_audio", related_audio_3, "-3")
        self.assert_max_speakers(related_audio_3, "3")
        related_audio_4 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-4")
        self.assert_related_audio_details("related_audio", related_audio_4, "-4")
        self.assert_max_speakers(related_audio_4, "4")
        related_audio_5 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-5")
        self.assert_related_audio_details("related_audio", related_audio_5, "-5")
        self.assert_max_speakers(related_audio_5, "5")

        related_image_1 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-1")
        self.assert_related_image_details("related_image", related_image_1, "-1")
        related_image_2 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-2")
        self.assert_related_image_details("related_image", related_image_2, "-2")
        related_image_3 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-3")
        self.assert_related_image_details("related_image", related_image_3, "-3")
        related_image_4 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-4")
        self.assert_related_image_details("related_image", related_image_4, "-4")
        related_image_5 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-5")
        self.assert_related_image_details("related_image", related_image_5, "-5")

        related_video_1 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-1")
        self.assert_related_video_details("related_video", related_video_1, "-1")
        related_video_2 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-2")
        self.assert_related_video_details("related_video", related_video_2, "-2")
        related_video_3 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-3")
        self.assert_related_video_details("related_video", related_video_3, "-3")
        related_video_4 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-4")
        self.assert_related_video_details("related_video", related_video_4, "-4")
        related_video_5 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-5")
        self.assert_related_video_details("related_video", related_video_5, "-5")

        related_document_1 = entry_1.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-1"
        )
        self.assert_related_document_details(
            "related_document", related_document_1, "-1"
        )
        related_document_2 = entry_1.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-2"
        )
        self.assert_related_document_details(
            "related_document", related_document_2, "-2"
        )
        related_document_3 = entry_1.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-3"
        )
        self.assert_related_document_details(
            "related_document", related_document_3, "-3"
        )
        related_document_4 = entry_1.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-4"
        )
        self.assert_related_document_details(
            "related_document", related_document_4, "-4"
        )
        related_document_5 = entry_1.related_documents.get(
            title=f"{self.DOCUMENT_TITLE}-5"
        )
        self.assert_related_document_details(
            "related_document", related_document_5, "-5"
        )

    def test_media_title_defaults_to_filename(self):
        self.confirm_upload_with_media_files("minimal_media.csv")

        entry_with_audio = DictionaryEntry.objects.filter(title="Word 1")[0]
        related_audio = entry_with_audio.related_audio.all()
        assert related_audio[0].title == "sample-audio.mp3"

        entry_with_image = DictionaryEntry.objects.filter(title="Phrase 1")[0]
        related_image = entry_with_image.related_images.all()
        assert related_image[0].title == "sample-image.jpg"

        entry_with_video = DictionaryEntry.objects.filter(title="Word 2")[0]
        related_video = entry_with_video.related_videos.all()
        assert related_video[0].title == "video_example_small.mp4"

        entry_with_document = DictionaryEntry.objects.filter(title="Phrase 2")[0]
        related_document = entry_with_document.related_documents.all()
        assert related_document[0].title == "sample-document.pdf"

    def test_duplicate_media_filenames(self):
        # If multiple rows have same filenames, only the first media instance will be imported
        # and used. The rest of the media will not be imported and should not give any issues.
        # All the latter entries will use the first imported media file.
        file_content = get_sample_file(
            "import_job/duplicate_media_filenames.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-document.pdf", "application/pdf"),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file("sample-image.jpg", "image/jpeg"),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file("video_example_small.mp4", "video/mp4"),
            import_job=import_job,
        )
        factories.PersonFactory.create(name="Test Speaker 1", site=self.site)
        factories.PersonFactory.create(name="Test Speaker 2", site=self.site)

        confirm_import_job(import_job.id)

        entry_1 = DictionaryEntry.objects.filter(title="Word 1")[0]
        related_audio_entry_1 = entry_1.related_audio.first()
        related_document_entry_1 = entry_1.related_documents.first()
        related_image_entry_1 = entry_1.related_images.first()
        related_video_entry_1 = entry_1.related_videos.first()

        entry_2 = DictionaryEntry.objects.filter(title="Phrase 1")[0]
        related_audio_entry_2 = entry_2.related_audio.first()
        related_document_entry_2 = entry_2.related_documents.first()
        related_image_entry_2 = entry_2.related_images.first()
        related_video_entry_2 = entry_2.related_videos.first()

        entry_3 = DictionaryEntry.objects.filter(title="Word 2")[0]
        related_audio_entry_3 = entry_3.related_audio.first()
        related_document_entry_3 = entry_3.related_documents.first()
        related_image_entry_3 = entry_3.related_images.first()
        related_video_entry_3 = entry_3.related_videos.first()

        assert related_audio_entry_1 == related_audio_entry_2 == related_audio_entry_3
        assert related_image_entry_1 == related_image_entry_2 == related_image_entry_3
        assert related_video_entry_1 == related_video_entry_2 == related_video_entry_3
        assert (
            related_document_entry_1
            == related_document_entry_2
            == related_document_entry_3
        )

    def test_unused_media_deleted(self):
        file_content = get_sample_file("import_job/minimal_media.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        # Adding media that is referenced in the csv
        audio_in_csv = factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )

        document_in_csv = factories.FileFactory(
            site=self.site,
            content=get_sample_file("sample-document.pdf", "application/pdf"),
            import_job=import_job,
        )

        image_in_csv = factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file("sample-image.jpg", "image/jpeg"),
            import_job=import_job,
        )

        video_in_csv = factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file("video_example_small.mp4", "video/mp4"),
            import_job=import_job,
        )

        # Adding additional media that is not in the csv
        factories.FileFactory(
            site=self.site,
            content=get_sample_file("import_job/Another audio.mp3", "audio/mpeg"),
            import_job=import_job,
        )

        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                "import_job/Another document.pdf", "application/pdf"
            ),
            import_job=import_job,
        )

        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file("import_job/Another image.jpg", "image/jpeg"),
            import_job=import_job,
        )

        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file("import_job/Another video.mp4", "video/mp4"),
            import_job=import_job,
        )

        confirm_import_job(import_job.id)

        images = ImageFile.objects.filter(import_job_id=import_job.id)
        files = File.objects.filter(import_job_id=import_job.id)
        videos = VideoFile.objects.filter(import_job_id=import_job.id)

        # Verifying only media included in csv are present after import job completion
        file_ids = list(files.values_list("id", flat=True))

        assert images.count() == 1 and images[0].id == image_in_csv.id
        assert files.count() == 2
        assert audio_in_csv.id in file_ids and document_in_csv.id in file_ids
        assert videos.count() == 1 and videos[0].id == video_in_csv.id

    def test_exception_deleting_unused_media(self, caplog):
        # Simulating a general exception when deleting unused media files

        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            status=JobStatus.ACCEPTED,
            validation_status=JobStatus.COMPLETE,
        )

        mock_objects = MagicMock()
        mock_objects.delete.side_effect = Exception("General Exception")
        with patch(
            "backend.tasks.import_job_tasks.File.objects.filter",
            return_value=mock_objects,
        ):
            confirm_import_job(import_job.id)

        assert (
            "An exception occurred while trying to delete unused media files."
            in caplog.text
        )

        updated_import_job = ImportJob.objects.filter(id=import_job.id).first()
        assert updated_import_job.status == JobStatus.COMPLETE

    def test_dictionary_entry_external_system_fields(self):
        external_system_1 = ExternalDictionaryEntrySystem(title="Fieldworks")
        external_system_1.save()
        external_system_2 = ExternalDictionaryEntrySystem(title="Dreamworks")
        external_system_2.save()

        file_content = get_sample_file(
            "import_job/dictionary_entry_external_system_fields.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        # Entry 1
        word = DictionaryEntry.objects.filter(title="abc")[0]
        assert word.external_system.title == external_system_1.title
        assert word.external_system_entry_id == "abc123"
        # Entry 2
        phrase = DictionaryEntry.objects.filter(title="xyz")[0]
        assert phrase.external_system.title == external_system_2.title
        assert phrase.external_system_entry_id == "xyz007"

    def test_related_media_ids_multiple(self):
        audio = factories.AudioFactory.create(id=TEST_AUDIO_IDS[0])
        factories.AudioFactory.create(id=TEST_AUDIO_IDS[1], site=audio.site)
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=audio.site)
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[1], site=audio.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=audio.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[1], site=audio.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=audio.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[1], site=audio.site)

        file_content = get_sample_file(
            "import_job/related_media_ids_multiple.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=audio.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 5

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 5
        entry1 = DictionaryEntry.objects.get(title="Multiple audio")
        assert entry1.related_audio.filter(id__in=TEST_AUDIO_IDS).count() == 2

        entry2 = DictionaryEntry.objects.get(title="Multiple image")
        assert entry2.related_images.filter(id__in=TEST_IMAGE_IDS).count() == 2

        entry3 = DictionaryEntry.objects.get(title="Multiple video")
        assert entry3.related_videos.filter(id__in=TEST_VIDEO_IDS).count() == 2

        entry4 = DictionaryEntry.objects.get(title="Multiple document")
        assert entry4.related_documents.filter(id__in=TEST_DOCUMENT_IDS).count() == 2

        entry4 = DictionaryEntry.objects.get(title="Multiple all media")
        assert entry4.related_audio.filter(id__in=TEST_AUDIO_IDS).count() == 2
        assert entry4.related_images.filter(id__in=TEST_IMAGE_IDS).count() == 2
        assert entry4.related_videos.filter(id__in=TEST_VIDEO_IDS).count() == 2
        assert entry4.related_documents.filter(id__in=TEST_DOCUMENT_IDS).count() == 2

    def test_related_media_mixed_multiple(self):
        file_content = get_sample_file(
            "import_job/related_media_mixed_multiple.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        self.upload_multiple_media_files(2, "related_audio", "audio", import_job)
        self.upload_multiple_media_files(2, "related_document", "document", import_job)
        self.upload_multiple_media_files(2, "related_image", "image", import_job)
        self.upload_multiple_media_files(2, "related_video", "video", import_job)

        factories.AudioFactory.create(id=TEST_AUDIO_IDS[0], site=self.site)
        factories.AudioFactory.create(id=TEST_AUDIO_IDS[1], site=self.site)
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=self.site)
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[1], site=self.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=self.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[1], site=self.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=self.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[1], site=self.site)

        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 5

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 5
        entry1 = DictionaryEntry.objects.get(title="Multiple audio")
        assert entry1.related_audio.filter(id__in=TEST_AUDIO_IDS).count() == 2
        assert entry1.related_audio.count() == 4

        entry2 = DictionaryEntry.objects.get(title="Multiple image")
        assert entry2.related_images.filter(id__in=TEST_IMAGE_IDS).count() == 2
        assert entry2.related_images.count() == 4

        entry3 = DictionaryEntry.objects.get(title="Multiple video")
        assert entry3.related_videos.filter(id__in=TEST_VIDEO_IDS).count() == 2
        assert entry3.related_videos.count() == 4

        entry4 = DictionaryEntry.objects.get(title="Multiple document")
        assert entry4.related_documents.filter(id__in=TEST_DOCUMENT_IDS).count() == 2
        assert entry4.related_documents.count() == 4

        entry5 = DictionaryEntry.objects.get(title="Multiple all media")
        assert entry5.related_audio.filter(id__in=TEST_AUDIO_IDS).count() == 2
        assert entry5.related_audio.count() == 4
        assert entry5.related_images.filter(id__in=TEST_IMAGE_IDS).count() == 2
        assert entry5.related_images.count() == 4
        assert entry5.related_videos.filter(id__in=TEST_VIDEO_IDS).count() == 2
        assert entry5.related_videos.count() == 4
        assert entry5.related_documents.filter(id__in=TEST_DOCUMENT_IDS).count() == 2
        assert entry5.related_documents.count() == 4

    def test_import_related_media_id_duplicate_ids(self):
        file_content = get_sample_file(
            "import_job/related_media_ids_multiple_duplicate.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )
        factories.AudioFactory.create(id=TEST_AUDIO_IDS[0], site=self.site)
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=self.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=self.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=self.site)
        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 5
        entry1 = DictionaryEntry.objects.get(title="Duplicate audio")
        assert entry1.related_audio.filter(id=TEST_AUDIO_IDS[0]).count() == 1
        assert entry1.related_audio.count() == 1

        entry2 = DictionaryEntry.objects.get(title="Duplicate image")
        assert entry2.related_images.filter(id=TEST_IMAGE_IDS[0]).count() == 1
        assert entry2.related_images.count() == 1

        entry3 = DictionaryEntry.objects.get(title="Duplicate video")
        assert entry3.related_videos.filter(id=TEST_VIDEO_IDS[0]).count() == 1
        assert entry3.related_videos.count() == 1

        entry4 = DictionaryEntry.objects.get(title="Duplicate document")
        assert entry4.related_documents.filter(id=TEST_DOCUMENT_IDS[0]).count() == 1
        assert entry4.related_documents.count() == 1

        entry5 = DictionaryEntry.objects.get(title="Duplicate all media")
        assert entry5.related_audio.filter(id=TEST_AUDIO_IDS[0]).count() == 1
        assert entry5.related_audio.count() == 1
        assert entry5.related_images.filter(id=TEST_IMAGE_IDS[0]).count() == 1
        assert entry5.related_images.count() == 1
        assert entry5.related_videos.filter(id=TEST_VIDEO_IDS[0]).count() == 1
        assert entry5.related_videos.count() == 1
        assert entry5.related_documents.filter(id=TEST_DOCUMENT_IDS[0]).count() == 1
        assert entry5.related_documents.count() == 1

    def test_import_related_media_id_mixed_invalid_and_valid(self):
        file_content = get_sample_file(
            "import_job/related_media_ids_multiple.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )
        factories.AudioFactory.create(id=TEST_AUDIO_IDS[0], site=self.site)
        factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=self.site)
        factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=self.site)
        factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=self.site)
        confirm_import_job(import_job.id)

        # All rows have invalid media ids, so no entries should be imported
        assert DictionaryEntry.objects.all().count() == 0

    def test_import_multiple_media_duplicate_filenames_same_row(self):
        file_content = get_sample_file(
            "import_job/related_media_multiple_duplicate_row.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        self.upload_multiple_media_files(2, "related_audio", "audio", import_job)

        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 1

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 1
        entry = DictionaryEntry.objects.get(title="Duplicate audio row")
        assert entry.related_audio.count() == 2

    def test_import_multiple_media_duplicate_filenames_same_col(self):
        file_content = get_sample_file(
            "import_job/related_media_multiple_duplicate_col.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        self.upload_multiple_media_files(4, "related_audio", "audio", import_job)

        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 3

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 3
        entry1 = DictionaryEntry.objects.get(title="Duplicate audio col 1")
        assert entry1.related_audio.count() == 3
        entry2 = DictionaryEntry.objects.get(title="Duplicate audio col 2")
        assert entry2.related_audio.count() == 2
        entry3 = DictionaryEntry.objects.get(title="Duplicate audio col 3")
        assert entry3.related_audio.count() == 3

    def test_import_multiple_media_mixed_invalid_and_valid_filenames(self):
        file_content = get_sample_file(
            "import_job/related_media_multiple_invalid.csv",
            self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        self.upload_multiple_media_files(1, "related_audio", "audio", import_job)

        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.error_rows == 1
        assert validation_report.new_rows == 0

        confirm_import_job(import_job.id)
        assert DictionaryEntry.objects.all().count() == 0

    def test_missing_media_multiple_rows_skipped(self):
        self.confirm_upload_with_media_files("missing_media_multiple.csv")
        assert DictionaryEntry.objects.all().count() == 0

    def test_import_video_embed_links(self):
        file_content = get_sample_file(
            "import_job/video_embed_links.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 3

        entry_1 = DictionaryEntry.objects.get(title="YouTube")
        assert len(entry_1.related_video_links) == 1
        assert entry_1.related_video_links[0] == YOUTUBE_VIDEO_LINK

        entry_2 = DictionaryEntry.objects.get(title="Vimeo")
        assert len(entry_2.related_video_links) == 1
        assert entry_2.related_video_links[0] == VIMEO_VIDEO_LINK

        entry_3 = DictionaryEntry.objects.get(title="Both")
        assert len(entry_3.related_video_links) == 2
        assert YOUTUBE_VIDEO_LINK in entry_3.related_video_links
        assert VIMEO_VIDEO_LINK in entry_3.related_video_links
