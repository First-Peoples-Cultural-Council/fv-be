import pytest

from backend.models import ImportJob
from backend.models.constants import Visibility
from backend.models.import_jobs import ImportJobMode
from backend.models.jobs import JobStatus
from backend.tasks.update_job_tasks import validate_update_job
from backend.tests import factories
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


@pytest.mark.django_db
class TestBulkUpdateDryRun:
    MIMETYPE = "text/csv"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def create_dictionary_entries(self, entry_ids):
        for entry_id in entry_ids:
            factories.DictionaryEntryFactory.create(
                id=entry_id,
                site=self.site,
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
        assert update_job.validation_report.new_rows == 2
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
        assert update_job.validation_report.new_rows == 6
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
        assert update_job.validation_report.new_rows == 3
        assert update_job.validation_report.error_rows == 0

    def test_invalid_update_values(self):
        self.create_dictionary_entries(TEST_ENTRY_IDS)

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
        error_rows_numbers = list(
            update_job.validation_report.rows.values_list("row_number", flat=True)
        )

        assert update_job.validation_status == JobStatus.COMPLETE
        assert update_job.validation_report.update_rows == 1
        assert update_job.validation_report.error_rows == 9
        assert error_rows_numbers == [2, 3, 4, 5, 6, 7, 8, 9, 10]
