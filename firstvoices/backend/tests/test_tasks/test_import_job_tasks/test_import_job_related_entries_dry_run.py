from uuid import UUID

import pytest

from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.models.import_jobs import ImportJob
from backend.models.jobs import JobStatus
from backend.tasks.import_job_tasks import validate_import_job
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportJobRelatedEntriesDryRun:
    MIMETYPE = "text/csv"
    MEDIA_FILES_DIR = "test_tasks/test_import_job_tasks/resources"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

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
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_related_entries_by_id.csv",
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

        assert validation_report.new_rows == 1
        assert validation_report.error_rows == 0

    def test_invalid_related_entries_by_id(self):
        # For entries that are already present in the db
        # Referring to a different model
        song = factories.SongFactory(
            site=self.site, id=UUID("d11ab39f-7767-4d34-9145-37c51006ba73")
        )

        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_invalid_related_entries_by_id.csv",
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
            f"Referenced dictionary entry not found for ID: {song.id}"
            in validation_error_rows[1].errors
        )

    def test_related_entries_by_title(self):
        # For entries from within the same batch import csv file
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_related_entries_by_title.csv",
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

    def test_related_entry_by_title_invalid_from_entry(self):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_related_entry_by_title_invalid_from_entry.csv",
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
        assert validation_report.new_rows == 1
        assert validation_report.error_rows == 1

        error_row = validation_report.rows.first()
        assert error_row.row_number == 1

        expected_error_message = (
            "Entry 'test_related_entry_by_title_invalid_from_entry_word_1' was not imported, "
            "and could not be linked as a related entry to "
            "entry 'test_related_entry_by_title_invalid_from_entry_word_2'. For related entries to be linked properly, "
            "please resolve the issues with entry 'test_related_entry_by_title_invalid_from_entry_word_1' "
            "before importing this file."
        )

        assert error_row.errors[1] == expected_error_message

    def test_related_entry_by_title_invalid_to_entry(self):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_related_entry_by_title_invalid_to_entry.csv",
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
        assert validation_report.new_rows == 0
        assert validation_report.error_rows == 2

        error_row = validation_report.rows.get(row_number=1)

        expected_error_message = (
            "Entry 'test_related_entry_by_title_invalid_to_entry_word_1' cannot be imported as related entry "
            "'test_related_entry_by_title_invalid_to_entry_word_2' could not be found to add as a related entry. "
            "Please resolve the problems with 'test_related_entry_by_title_invalid_to_entry_word_2' before "
            "attempting the import again."
        )

        assert error_row.errors[0] == expected_error_message

    def test_related_entry_by_title_invalid_both_entries(self):
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_related_entry_by_title_invalid_both_entries.csv",
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
        assert validation_report.new_rows == 1  # Control row present
        assert validation_report.error_rows == 2

        error_rows = validation_report.rows.all().order_by("row_number")
        error_row_1 = error_rows[0]
        error_row_2 = error_rows[1]

        assert error_row_1.row_number == 1
        assert error_row_2.row_number == 2

        assert len(error_row_1.errors) == 2
        assert (
            "Entry 'test_related_entry_by_title_invalid_both_entries_word_1' was not imported, and could not be "
            "linked as a related entry to entry 'test_related_entry_by_title_invalid_both_entries_word_2'. "
            "For related entries to be linked properly, please resolve the issues with "
            "entry 'test_related_entry_by_title_invalid_both_entries_word_1' before "
            "importing this file." in error_row_1.errors[1]
        )

        assert len(error_row_2.errors) == 2
        assert (
            "Entry 'test_related_entry_by_title_invalid_both_entries_word_2' was not imported, and could not be "
            "linked as a related entry to entry 'test_related_entry_by_title_invalid_both_entries_word_1'. "
            "For related entries to be linked properly, please resolve the issues with "
            "entry 'test_related_entry_by_title_invalid_both_entries_word_2' before "
            "importing this file." in error_row_2.errors[1]
        )

    def test_related_entries_duplicate_titles_same_row(self):
        # if a related entry title appears in the same row multiple times, fail the row
        file_content = get_sample_file(
            file_dir=self.MEDIA_FILES_DIR,
            filename="test_related_entries_duplicate_titles_same_row.csv",
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
        assert validation_report.new_rows == 1
        assert validation_report.error_rows == 1

        error_row = validation_report.rows.first()
        assert error_row.row_number == 1
        assert (
            "Duplicate related entry title 'test_related_entries_duplicate_titles_same_row_word_2' found in "
            "column 'related_entry_2'. Please ensure each related entry title is unique per entry."
        )
