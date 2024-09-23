from unittest.mock import patch
from uuid import UUID

import pytest
import tablib

from backend.models import DictionaryEntry, ImportJob
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.models.import_jobs import JobStatus
from backend.tasks.import_job_tasks import batch_import
from backend.tests.factories import (
    DictionaryEntryFactory,
    FileFactory,
    ImportJobFactory,
    SiteFactory,
    SongFactory,
)
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestBulkImportDryRun:
    MIMETYPE = "text/csv"

    def import_invalid_dictionary_entries(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file(
            "import_job/invalid_dictionary_entries.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        batch_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)

        return import_job_instance

    def test_import_task_logs(self, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        batch_import(import_job_instance.id)

        assert (
            f"Task started. Additional info: import_job_instance_id: {import_job_instance.id}, dry-run: True."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_base_case_dictionary_entries(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        batch_import(import_job_instance.id)

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

        batch_import(import_job_instance.id)

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
            "TRANSLATION_2",
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
        import_job_instance = self.import_invalid_dictionary_entries()
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

        batch_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report
        error_rows = validation_report.rows.all()
        error_rows_numbers = list(
            validation_report.rows.values_list("row_number", flat=True)
        )

        assert len(error_rows) == 3
        assert error_rows_numbers == [3, 4, 5]

    def test_validation_report_columns(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file("import_job/unknown_columns.csv", self.MIMETYPE)
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        batch_import(import_job_instance.id)

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

        batch_import(import_job_instance.id)

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

        batch_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report

        assert validation_report.new_rows == 12
        assert validation_report.error_rows == 1
        assert validation_report.skipped_rows == 0

        validation_error_row = validation_report.rows.first()
        assert validation_error_row.row_number == 13
        assert (
            "Invalid value in include_on_kids_site column. Expected 'true' or 'false'."
            in validation_error_row.errors
        )

    def test_existing_related_entries(self):
        # For entries that are already present in the db
        site = SiteFactory(visibility=Visibility.PUBLIC)
        DictionaryEntryFactory(
            site=site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )
        DictionaryEntryFactory(
            site=site,
            type=TypeOfDictionaryEntry.PHRASE,
            id=UUID("f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d"),
        )

        file_content = get_sample_file(
            "import_job/valid_related_entries.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        batch_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report

        assert validation_report.new_rows == 2
        assert validation_report.error_rows == 0
        assert validation_report.skipped_rows == 0

    def test_invalid_related_entries(self):
        # For entries that are already present in the db
        site = SiteFactory(visibility=Visibility.PUBLIC)
        # Referring to a different model
        SongFactory(site=site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c"))

        file_content = get_sample_file(
            "import_job/invalid_related_entries.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(site=site, data=file)

        batch_import(import_job_instance.id)

        # Updated instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        validation_report = import_job_instance.validation_report

        assert validation_report.new_rows == 0
        assert validation_report.error_rows == 2
        assert validation_report.skipped_rows == 0

        validation_error_rows = validation_report.rows.all().order_by("row_number")

        assert validation_error_rows[0].row_number == 1
        assert (
            "Invalid DictionaryEntry supplied in column: related_entry. Expected field: id"
            in validation_error_rows[0].errors
        )

        assert validation_error_rows[1].row_number == 2
        assert (
            "No DictionaryEntry found with the provided id in column related_entry."
            in validation_error_rows[1].errors
        )

    def test_dry_run_failed(self, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        file = FileFactory(
            content=get_sample_file("import_job/all_valid_columns.csv", self.MIMETYPE)
        )

        # Mock that the task has already completed
        import_job_instance = ImportJobFactory(site=site, data=file)

        with patch(
            "backend.tasks.import_job_tasks.import_resource",
            side_effect=Exception("Random exception."),
        ):
            batch_import(import_job_instance.id)

            # Updated import job instance
            import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
            assert import_job_instance.validation_status == JobStatus.FAILED
            assert "Random exception." in caplog.text

    def test_failed_rows_csv(self):
        import_job_instance = self.import_invalid_dictionary_entries()
        validation_report = import_job_instance.validation_report
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
            import_job_instance.failed_rows_csv.content.read().decode("utf-8-sig"),
            format="csv",
        )

        assert len(failed_rows_csv_table) == 5

        for i in range(0, len(error_rows_numbers)):
            input_index = (
                error_rows_numbers[i] - 1
            )  # since we do +1 while generating error row numbers
            assert input_csv_table[input_index] == failed_rows_csv_table[i]


@pytest.mark.django_db
class TestBulkImport:
    MIMETYPE = "text/csv"

    def test_import_task_logs(self, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=JobStatus.COMPLETE
        )

        batch_import(import_job_instance.id, dry_run=False)

        assert (
            f"Task started. Additional info: import_job_instance_id: {import_job_instance.id}, dry-run: False."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_base_case_dictionary_entries(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=JobStatus.COMPLETE
        )

        batch_import(import_job_instance.id, dry_run=False)

        # word
        word = DictionaryEntry.objects.filter(site=site, title="abc")[0]
        assert word.type == TypeOfDictionaryEntry.WORD

        # phrase
        phrase = DictionaryEntry.objects.filter(site=site, title="xyz")[0]
        assert phrase.type == TypeOfDictionaryEntry.PHRASE

    def test_all_columns_dictionary_entries(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file(
            "import_job/all_valid_columns.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=JobStatus.COMPLETE
        )

        batch_import(import_job_instance.id, dry_run=False)

        # Verifying first entry
        first_entry = DictionaryEntry.objects.filter(site=site, title="Word 1")[0]
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

    def test_parallel_jobs_not_allowed(self, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        file = FileFactory(
            content=get_sample_file("import_job/all_valid_columns.csv", self.MIMETYPE)
        )
        same_file = FileFactory(
            content=get_sample_file("import_job/all_valid_columns.csv", self.MIMETYPE)
        )  # Since it's a OneToOne field, can't use a file again

        ImportJobFactory(
            site=site,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.STARTED,
        )
        import_job_instance = ImportJobFactory(
            site=site, data=same_file, validation_status=JobStatus.COMPLETE
        )

        batch_import(import_job_instance.id, dry_run=False)

        # Updated import job instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        assert import_job_instance.status == JobStatus.CANCELLED
        assert (
            "There is at least 1 already on-going job on this site. "
            "Please wait for it to finish before starting a new one." in caplog.text
        )

    @pytest.mark.parametrize("status", [JobStatus.COMPLETE, JobStatus.FAILED])
    def test_task_already_completed(self, status, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        file = FileFactory(
            content=get_sample_file("import_job/all_valid_columns.csv", self.MIMETYPE)
        )

        # Mock that the task has already completed
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=JobStatus.COMPLETE, status=status
        )

        batch_import(import_job_instance.id, dry_run=False)

        assert (
            "The job has already been executed once. "
            "Please create another batch request to import the entries." in caplog.text
        )

    @pytest.mark.parametrize(
        "validation_status",
        [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.FAILED, JobStatus.CANCELLED],
    )
    def test_confirm_not_allowed_for_invalid_dry_run(self, validation_status, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        file = FileFactory(
            content=get_sample_file("import_job/all_valid_columns.csv", self.MIMETYPE)
        )

        # Mock that the task has already completed
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=validation_status
        )

        batch_import(import_job_instance.id, dry_run=False)

        # Updated import job instance
        import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
        assert import_job_instance.status == JobStatus.CANCELLED
        assert (
            "A successful dry-run is required before doing the import. "
            "Please fix any issues found during the dry-run of the CSV file and run a new batch."
            in caplog.text
        )

    def test_import_job_failed(self, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        file = FileFactory(
            content=get_sample_file("import_job/all_valid_columns.csv", self.MIMETYPE)
        )

        # Mock that the task has already completed
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=JobStatus.COMPLETE
        )

        with patch(
            "backend.tasks.import_job_tasks.import_resource",
            side_effect=Exception("Random exception."),
        ):
            batch_import(import_job_instance.id, dry_run=False)

            # Updated import job instance
            import_job_instance = ImportJob.objects.get(id=import_job_instance.id)
            assert import_job_instance.status == JobStatus.FAILED
            assert "Random exception." in caplog.text

    def test_existing_related_entries(self):
        # For entries that are already present in the db
        site = SiteFactory(visibility=Visibility.PUBLIC)
        existing_entry = DictionaryEntryFactory(
            site=site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )

        file_content = get_sample_file(
            "import_job/valid_related_entries.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=JobStatus.COMPLETE
        )

        batch_import(import_job_instance.id, dry_run=False)

        new_entry = DictionaryEntry.objects.get(title="Word 1")
        related_entry = new_entry.dictionaryentrylink_set.first()

        assert related_entry.from_dictionary_entry.id == new_entry.id
        assert related_entry.to_dictionary_entry.id == existing_entry.id

    def test_multiple_existing_related_entries(self):
        # For entries that are already present in the db
        site = SiteFactory(visibility=Visibility.PUBLIC)
        existing_entry_1 = DictionaryEntryFactory(
            site=site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )
        existing_entry_2 = DictionaryEntryFactory(
            site=site,
            type=TypeOfDictionaryEntry.PHRASE,
            id=UUID("f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d"),
        )

        file_content = get_sample_file(
            "import_job/valid_related_entries.csv", self.MIMETYPE
        )
        file = FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=JobStatus.COMPLETE
        )

        batch_import(import_job_instance.id, dry_run=False)

        related_entry = DictionaryEntry.objects.get(
            title="Word 2"
        ).dictionaryentrylink_set.values_list("to_dictionary_entry_id", flat=True)
        related_entry_list = list(related_entry)

        assert existing_entry_1.id in related_entry_list
        assert existing_entry_2.id in related_entry_list
