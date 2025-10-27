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
]


@pytest.mark.django_db
class TestBulkUpdateDryRun:
    MIMETYPE = "text/csv"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def update_minimal_dictionary_entries(self, entry_ids):
        for entry_id in entry_ids:
            factories.DictionaryEntryFactory.create(
                id=entry_id,
                site=self.site,
            )

        file_content = get_sample_file("update_job/minimal_update.csv", self.MIMETYPE)
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
