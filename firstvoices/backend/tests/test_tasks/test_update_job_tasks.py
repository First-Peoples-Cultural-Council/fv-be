import uuid
from unittest.mock import patch
from uuid import UUID

import pytest
import tablib

from backend.models import ImportJob
from backend.models.constants import Visibility
from backend.models.dictionary import DictionaryEntry, ExternalDictionaryEntrySystem
from backend.models.import_jobs import ImportJobMode
from backend.models.jobs import JobStatus
from backend.tasks.update_job_tasks import confirm_update_job, validate_update_job
from backend.tests import factories
from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin
from backend.tests.utils import get_sample_file

TEST_ENTRY_IDS = [
    "ba93662a-e1bc-4c0b-8fa1-12b0bc108be1",
    "768c920c-38a9-4aea-821a-e1c0739c00d4",
    "67525f1e-2a55-40b6-b39c-cb708819f47c",
    "adcc9c74-3ab2-4a31-8063-5ba5007be507",
    "6398bfb3-7d4a-48ce-9286-0408ea183043",
    "bc525519-77ef-4318-94a6-cd9fc85f8646",
    "7120e5f5-de3a-48fd-a697-1529e2fbe3c3",
    "92782704-d2c9-47fc-b628-abdca150ed54",
]


def setup_for_external_systems(site):
    external_system_1 = ExternalDictionaryEntrySystem(title="Dreamworks")
    external_system_1.save()
    external_system_2 = ExternalDictionaryEntrySystem(title="Fieldworks")
    external_system_2.save()

    factories.DictionaryEntryFactory.create(
        id="ba93662a-e1bc-4c0b-8fa1-12b0bc108be1",
        site=site,
        external_system=external_system_1,
        external_system_entry_id="FW123",
    )

    file_content = get_sample_file("update_job/external_system_fields.csv", "text/csv")
    file = factories.FileFactory(content=file_content)
    return external_system_1, external_system_2, file


@pytest.mark.django_db
class TestBulkUpdateDryRun:
    MIMETYPE = "text/csv"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def create_dictionary_entries(self, entry_ids, site=None):
        if site is None:
            site = self.site
        for entry_id in entry_ids:
            factories.DictionaryEntryFactory.create(
                id=entry_id,
                site=site,
            )

    def update_minimal_dictionary_entries(self, entry_ids):
        self.create_dictionary_entries(entry_ids)

        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)

        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)
        return update_job

    def update_invalid_dictionary_entries(self, entry_ids):
        self.create_dictionary_entries(entry_ids)

        file_content = get_sample_file(
            "update_job/invalid_dictionary_entry_updates.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)

        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)
        return update_job

    def validate_related_entries(self):
        file_content = get_sample_file(
            "update_job/related_entries_by_id_add_new_entries.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)

        update_job = ImportJob.objects.get(id=update_job.id)
        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 1
        assert update_job.validation_report.error_rows == 0

    def test_update_task_logs(self, caplog):
        update_job = self.update_minimal_dictionary_entries(TEST_ENTRY_IDS)

        assert (
            f"Task started. Additional info: Update job id: {update_job.id}, dry-run: True."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_base_case_update(self):
        update_job = self.update_minimal_dictionary_entries(TEST_ENTRY_IDS)

        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 2
        assert update_job.validation_report.error_rows == 0

    def test_all_columns_update(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)

        file_content = get_sample_file(
            "update_job/all_valid_columns.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)

        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)

        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 6
        assert update_job.validation_report.error_rows == 0

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
            assert column in update_job.validation_report.accepted_columns

        assert len(update_job.validation_report.ignored_columns) == 0

    def test_default_update_values(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)

        file_content = get_sample_file("update_job/default_values.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)

        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)

        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 3
        assert update_job.validation_report.error_rows == 0

    def test_invalid_update_values(self):
        update_job = self.update_invalid_dictionary_entries(TEST_ENTRY_IDS)

        error_rows_numbers = list(
            update_job.validation_report.rows.values_list("row_number", flat=True)
        )

        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 1
        assert update_job.validation_report.error_rows == 9
        assert error_rows_numbers == [2, 3, 4, 5, 6, 7, 8, 9, 10]

    def test_dry_run_failed(self, caplog):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file = factories.FileFactory(
            content=get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        )

        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        with patch(
            "backend.tasks.update_job_tasks.process_update_job_data",
            side_effect=Exception("Test exception"),
        ):
            validate_update_job(update_job.id)

            update_job = ImportJob.objects.get(id=update_job.id)
            assert update_job.validation_status == JobStatus.FAILED
            assert "Test exception" in caplog.text

    def test_failed_rows_csv(self):
        update_job = self.update_invalid_dictionary_entries(TEST_ENTRY_IDS)
        error_rows_numbers = list(
            update_job.validation_report.rows.values_list("row_number", flat=True)
        )

        file_content = get_sample_file(
            "update_job/invalid_dictionary_entry_updates.csv", self.MIMETYPE
        )
        input_csv_table = tablib.Dataset().load(
            file_content.read().decode("utf-8-sig"), format="csv"
        )

        failed_rows_csv_table = tablib.Dataset().load(
            update_job.failed_rows_csv.content.read().decode("utf-8-sig"),
            format="csv",
        )

        assert update_job.validation_report.error_rows == 9
        assert error_rows_numbers == [2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert len(failed_rows_csv_table) == 9

        for i in range(0, len(error_rows_numbers)):
            input_index = (
                error_rows_numbers[i] - 1
            )  # since we do +1 while generating error row numbers
            assert input_csv_table[input_index] == failed_rows_csv_table[i]

    def test_failed_rows_csv_not_generated_on_valid_rows(self):
        update_job = self.update_minimal_dictionary_entries(TEST_ENTRY_IDS)
        assert update_job.failed_rows_csv is None

    @pytest.mark.parametrize(
        "validation_status",
        [None, JobStatus.STARTED, JobStatus.COMPLETE, JobStatus.FAILED],
    )
    def test_invalid_validation_status(self, validation_status, caplog):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=validation_status,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)
        assert update_job.validation_status == JobStatus.FAILED
        assert "This job cannot be run due to consistency issues." in caplog.text

    @pytest.mark.parametrize(
        "status", [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE]
    )
    def test_invalid_job_status(self, status, caplog):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            status=status,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)
        assert update_job.validation_status == JobStatus.FAILED
        assert (
            "This job could not be started as it is either queued, or already running or completed. "
            f"Update job id: {update_job.id}." in caplog.text
        )

    def test_update_dictionary_entry_external_system_fields(self):
        _, _, file = setup_for_external_systems(self.site)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )
        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)
        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 1
        assert update_job.validation_report.error_rows == 0

    @pytest.mark.parametrize(
        "site_visibility, expected_updated_rows, expected_error_rows",
        [
            (Visibility.PUBLIC, 3, 1),
            (Visibility.MEMBERS, 2, 2),
            (Visibility.TEAM, 1, 3),
        ],
    )
    def test_invalid_site_visibility(
        self, site_visibility, expected_updated_rows, expected_error_rows
    ):
        site = factories.SiteFactory(visibility=site_visibility)
        self.create_dictionary_entries(TEST_ENTRY_IDS, site=site)

        file_content = get_sample_file(
            "update_job/visibility_values.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)

        update_job = factories.ImportJobFactory(
            site=site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)

        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == expected_updated_rows
        assert update_job.validation_report.error_rows == expected_error_rows

    def test_updated_entries_not_in_site(self):
        other_site = factories.SiteFactory()
        self.create_dictionary_entries(TEST_ENTRY_IDS, site=other_site)

        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)

        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)

        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 0
        assert update_job.validation_report.error_rows == 2

    def test_update_only_one_column(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)

        file_content = get_sample_file(
            "update_job/one_column_update.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)

        update_job = ImportJob.objects.get(id=update_job.id)
        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 2
        assert update_job.validation_report.error_rows == 0

    def test_duplicate_ids_in_update_file(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/duplicate_ids.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        validate_update_job(update_job.id)

        update_job = ImportJob.objects.get(id=update_job.id)
        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.updated_rows == 1
        assert update_job.validation_report.error_rows == 1

    def test_related_entries_by_id_new_entries(self):
        # Adding an entry with no related entries
        factories.DictionaryEntryFactory(
            site=self.site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )

        # Entry to be added as the related entry
        # For entries that are already present in the db
        factories.DictionaryEntryFactory(
            site=self.site, id=UUID("f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d")
        )

        self.validate_related_entries()

    def test_related_entries_by_id_replace_existing_entries(self):
        # Adding an entry with no related entries
        existing_related_entry = factories.DictionaryEntryFactory(site=self.site)
        primary_entry = factories.DictionaryEntryFactory(
            site=self.site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )
        primary_entry.related_dictionary_entries.add(existing_related_entry)
        primary_entry.save()

        # Entry to be added as the related entry
        # For entries that are already present in the db
        factories.DictionaryEntryFactory(
            site=self.site, id=UUID("f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d")
        )

        self.validate_related_entries()


@pytest.mark.django_db
class TestBulkUpdate(IgnoreTaskResultsMixin):
    MIMETYPE = "text/csv"
    TASK = confirm_update_job

    def get_valid_task_args(self):
        return (uuid.uuid4(),)

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def create_dictionary_entries(self, entry_ids, site=None):
        if site is None:
            site = self.site
        for entry_id in entry_ids:
            factories.DictionaryEntryFactory.create(
                id=entry_id,
                site=site,
            )

    def test_update_task_logs(self, caplog):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        confirm_update_job(update_job.id)

        assert (
            f"Task started. Additional info: Update job id: {update_job.id}, dry-run: False."
            in caplog.text
        )
        assert "Task ended." in caplog.text

    def test_base_case_update(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )
        confirm_update_job(update_job.id)

        entry1 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[0])
        assert entry1.title == "abc"
        assert entry1.type == "word"

        entry2 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[1])
        assert entry2.title == "xyz"
        assert entry2.type == "phrase"

    def test_all_columns_update(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file(
            "update_job/all_valid_columns.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )
        confirm_update_job(update_job.id)
        entry = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[0])
        assert entry.title == "Word 1"
        assert entry.type == "word"
        assert entry.visibility == Visibility.PUBLIC
        assert entry.part_of_speech.title == "Adjective"
        assert entry.exclude_from_games is False
        assert entry.exclude_from_kids is True
        assert entry.translations == [
            "first_translation",
            "second_translation",
            "third_translation",
            "fourth_translation",
            "fifth_translation",
        ]
        assert entry.acknowledgements == [
            "first_ack",
            "second_ack",
            "third_ack",
            "fourth_ack",
            "fifth_ack",
        ]
        assert entry.notes == [
            "first_note",
            "second_note",
            "third_note",
            "fourth_note",
            "fifth_note",
        ]
        assert entry.alternate_spellings == [
            "alt_s_1",
            "alt_s_2",
            "alt_s_3",
            "alt_s_4",
            "alt_s_5",
        ]
        assert entry.pronunciations == [
            "first_p",
            "second_p",
            "third_p",
            "fourth_p",
            "fifth_p",
        ]

        categories = list(entry.categories.all().values_list("title", flat=True))
        assert "Animals" in categories
        assert "Body" in categories

    def test_update_default_values(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/default_values.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )
        confirm_update_job(update_job.id)

        entry1 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[0])
        assert entry1.visibility == Visibility.TEAM
        assert entry1.exclude_from_games is True
        assert entry1.exclude_from_kids is False

        entry2 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[1])
        assert entry2.visibility == Visibility.PUBLIC
        assert entry2.exclude_from_games is False
        assert entry2.exclude_from_kids is False

        entry3 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[2])
        assert entry3.visibility == Visibility.TEAM
        assert entry3.exclude_from_games is True
        assert entry3.exclude_from_kids is False

    def test_update_job_failed(self, caplog):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        with patch(
            "backend.tasks.update_job_tasks.process_update_job_data",
            side_effect=Exception("Test exception"),
        ):
            confirm_update_job(update_job.id)

            update_job = ImportJob.objects.get(id=update_job.id)
            assert update_job.status == JobStatus.FAILED
            assert "Test exception" in caplog.text

    def test_update_valid_rows_only(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file(
            "update_job/invalid_dictionary_entry_updates.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )
        confirm_update_job(update_job.id)

        entry = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[0])
        assert entry.title == "Control"

        entry2 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[1])
        assert entry2.title != "Invalid type"

    @pytest.mark.parametrize(
        "status", [None, JobStatus.STARTED, JobStatus.COMPLETE, JobStatus.FAILED]
    )
    def test_invalid_status(self, status, caplog):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=status,
            mode=ImportJobMode.UPDATE,
        )

        confirm_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)
        assert update_job.status == JobStatus.FAILED
        assert "This job cannot be run due to consistency issues." in caplog.text

    @pytest.mark.parametrize(
        "validation_status",
        [None, JobStatus.STARTED, JobStatus.ACCEPTED, JobStatus.FAILED],
    )
    def test_invalid_validation_status(self, validation_status, caplog):
        self.create_dictionary_entries(TEST_ENTRY_IDS)
        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=validation_status,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        confirm_update_job(update_job.id)
        update_job = ImportJob.objects.get(id=update_job.id)
        assert update_job.status == JobStatus.FAILED
        assert (
            f"Please validate the job before confirming the import. Update job id: {update_job.id}."
            in caplog.text
        )

    def test_update_dictionary_entry_external_system_fields(self):
        _, external_system_2, file = setup_for_external_systems(self.site)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )
        confirm_update_job(update_job.id)

        entry = DictionaryEntry.objects.get(id="ba93662a-e1bc-4c0b-8fa1-12b0bc108be1")
        assert entry.external_system == external_system_2
        assert entry.external_system_entry_id == "abc123"

    def test_missing_update_columns_unchanged(self):
        factories.DictionaryEntryFactory.create(
            id="ba93662a-e1bc-4c0b-8fa1-12b0bc108be1",
            site=self.site,
            title="Word 1",
            type="word",
            visibility=Visibility.PUBLIC,
        )

        factories.DictionaryEntryFactory.create(
            id="768c920c-38a9-4aea-821a-e1c0739c00d4",
            site=self.site,
            title="Word 2",
            type="word",
            visibility=Visibility.MEMBERS,
        )

        file_content = get_sample_file("update_job/minimal.csv", self.MIMETYPE)
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )
        confirm_update_job(update_job.id)

        entry1 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[0])
        assert entry1.title == "abc"
        assert entry1.type == "word"
        assert entry1.visibility == Visibility.PUBLIC  # unchanged

        entry2 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[1])
        assert entry2.title == "xyz"
        assert entry2.type == "phrase"
        assert entry2.visibility == Visibility.MEMBERS  # unchanged

    def test_update_only_one_column(self):
        factories.DictionaryEntryFactory.create(
            id="ba93662a-e1bc-4c0b-8fa1-12b0bc108be1",
            site=self.site,
            exclude_from_games=False,
        )
        factories.DictionaryEntryFactory.create(
            id="768c920c-38a9-4aea-821a-e1c0739c00d4",
            site=self.site,
            exclude_from_games=True,
        )

        file_content = get_sample_file(
            "update_job/one_column_update.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        confirm_update_job(update_job.id)
        entry1 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[0])
        assert entry1.exclude_from_games

        entry2 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[1])
        assert not entry2.exclude_from_games

    def test_valid_blank_columns_cleared(self):
        factories.DictionaryEntryFactory.create(
            id="ba93662a-e1bc-4c0b-8fa1-12b0bc108be1",
            site=self.site,
            title="Word 1",
            type="word",
            visibility=Visibility.PUBLIC,
            translations=["hello", "hi"],
        )
        factories.DictionaryEntryFactory.create(
            id="768c920c-38a9-4aea-821a-e1c0739c00d4",
            site=self.site,
            title="Word 2",
            type="word",
            visibility=Visibility.MEMBERS,
            translations=["goodbye"],
        )

        file_content = get_sample_file(
            "update_job/blank_optional_columns.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        confirm_update_job(update_job.id)
        entry1 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[0])
        assert entry1.title == "Word 1"  # unchanged
        assert entry1.type == "word"  # unchanged
        assert entry1.translations == ["new translation"]  # updated

        entry2 = DictionaryEntry.objects.get(id=TEST_ENTRY_IDS[1])
        assert entry2.title == "Word 2"  # unchanged
        assert entry2.type == "word"  # unchanged
        assert entry2.translations == []  # cleared

    def test_related_entries_by_id_new_entries(self):
        # Adding an entry with no related entries
        primary_entry = factories.DictionaryEntryFactory(
            site=self.site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )

        # Entry to be added as the related entry
        # For entries that are already present in the db
        new_related_entry = factories.DictionaryEntryFactory(
            site=self.site, id=UUID("f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d")
        )

        file_content = get_sample_file(
            "update_job/related_entries_by_id_add_new_entries.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        confirm_update_job(update_job.id)
        primary_entry = DictionaryEntry.objects.get(id=primary_entry.id)
        related_entries = primary_entry.related_dictionary_entries.all().values_list(
            "id", flat=True
        )
        assert new_related_entry.id in related_entries

    def test_related_entries_by_id_replace_existing_entries(self):
        # Adding an entry with no related entries
        existing_related_entry = factories.DictionaryEntryFactory(site=self.site)
        primary_entry = factories.DictionaryEntryFactory(
            site=self.site, id=UUID("964b2b52-45c3-4c2f-90db-7f34c6599c1c")
        )
        primary_entry.related_dictionary_entries.add(existing_related_entry)
        primary_entry.save()

        # Entry to be added as the related entry
        # For entries that are already present in the db
        new_related_entry = factories.DictionaryEntryFactory(
            site=self.site, id=UUID("f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d")
        )
        new_related_entry_2 = factories.DictionaryEntryFactory(
            site=self.site, id=UUID("02507a2e-d18a-4277-b0c2-21d59764be13")
        )

        file_content = get_sample_file(
            "update_job/related_entries_by_id_replace_entries.csv", self.MIMETYPE
        )
        file = factories.FileFactory(content=file_content)
        update_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
            mode=ImportJobMode.UPDATE,
        )

        confirm_update_job(update_job.id)
        primary_entry = DictionaryEntry.objects.get(id=primary_entry.id)
        related_entries = primary_entry.related_dictionary_entries.all().values_list(
            "id", flat=True
        )
        assert existing_related_entry.id not in related_entries
        assert new_related_entry.id in related_entries
        assert new_related_entry_2.id in related_entries
