from unittest.mock import patch

import pytest

from backend.models import DictionaryEntry, ImportJob
from backend.models.constants import Visibility
from backend.models.dictionary import (
    ExternalDictionaryEntrySystem,
    TypeOfDictionaryEntry,
)
from backend.models.import_jobs import JobStatus
from backend.tasks.import_job_tasks import confirm_import_job
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportJob:
    MIMETYPE = "text/csv"
    CSV_FILES_DIR = "test_tasks/test_import_job_tasks/resources"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def test_import_task_logs(self, caplog):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_task_logs.csv",
            mimetype=self.MIMETYPE,
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

        assert (
            f"Task started. Additional info: ImportJob id: {import_job.id}, dry-run: False."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_failed_job(self, caplog):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_failed_job.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)

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

    def test_base_case_dictionary_entries(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_base_case_dictionary_entries.csv",
            mimetype=self.MIMETYPE,
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

        # word
        word = DictionaryEntry.objects.get(
            title="test_base_case_dictionary_entries_word_1"
        )
        assert word.type == TypeOfDictionaryEntry.WORD
        assert word.created_by == self.user
        assert word.last_modified_by == self.user
        assert word.system_last_modified >= word.last_modified
        assert word.system_last_modified_by == import_job.created_by
        # phrase
        phrase = DictionaryEntry.objects.get(
            title="test_base_case_dictionary_entries_phrase_1"
        )
        assert phrase.type == TypeOfDictionaryEntry.PHRASE
        assert phrase.created_by == self.user
        assert phrase.last_modified_by == self.user
        assert phrase.system_last_modified >= phrase.last_modified
        assert phrase.system_last_modified_by == import_job.created_by

    def test_all_non_media_columns_dictionary_entries(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_all_non_media_columns_dictionary_entries.csv",
            mimetype=self.MIMETYPE,
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
        first_entry = DictionaryEntry.objects.get(
            title="test_all_non_media_columns_word_1"
        )
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
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_default_values.csv",
            mimetype=self.MIMETYPE,
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

        # Verifying default type
        empty_type = DictionaryEntry.objects.get(title="test_default_values_empty_type")
        assert empty_type.type == TypeOfDictionaryEntry.WORD

        # default visibility
        empty_visibility = DictionaryEntry.objects.get(
            title="test_default_values_empty_visibility"
        )
        assert empty_visibility.visibility == Visibility.TEAM

        # default audience flags
        empty_games_flag = DictionaryEntry.objects.get(
            title="test_default_values_empty_include_in_games"
        )
        assert empty_games_flag.exclude_from_games is False
        empty_kids_flag = DictionaryEntry.objects.get(
            title="test_default_values_empty_include_on_kids_site"
        )
        assert empty_kids_flag.exclude_from_kids is False

    def test_import_job_added_to_imported_entries(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_import_job_added_to_imported_entries.csv",
            mimetype=self.MIMETYPE,
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

        # word
        word = DictionaryEntry.objects.get(
            title="test_import_job_added_to_import_entries_word_1"
        )
        assert word.import_job == import_job

        # phrase
        phrase = DictionaryEntry.objects.get(
            title="test_import_job_added_to_import_entries_phrase_1"
        )
        assert phrase.import_job == import_job

    @pytest.mark.parametrize(
        "status", [None, JobStatus.STARTED, JobStatus.COMPLETE, JobStatus.FAILED]
    )
    def test_invalid_status(self, status, caplog):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_invalid_status.csv",
            mimetype=self.MIMETYPE,
        )
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
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_invalid_validation_status.csv",
            mimetype=self.MIMETYPE,
        )
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
