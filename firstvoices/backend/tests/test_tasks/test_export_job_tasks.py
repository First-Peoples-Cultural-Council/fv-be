import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import connection

from backend.models.files import File
from backend.models.jobs import ExportJob, JobStatus
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE
from backend.tasks.export_job_tasks import delete_old_exports, generate_export_csv
from backend.tests import factories
from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin


@pytest.mark.django_db
class TestExportJob(IgnoreTaskResultsMixin):
    TASK = generate_export_csv

    def get_valid_task_args(self):
        return (uuid.uuid4(),)

    def assert_caplog_text(self, caplog, job_id):
        assert ASYNC_TASK_START_TEMPLATE % f"ExportJob id: {job_id}" in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    def test_generate_export_csv_invalid_id(self, caplog):
        invalid_id = uuid.uuid4()
        with pytest.raises(ExportJob.DoesNotExist):
            generate_export_csv(str(invalid_id))

        assert ASYNC_TASK_START_TEMPLATE % f"ExportJob id: {invalid_id}" in caplog.text

    @pytest.mark.parametrize("status", [JobStatus.STARTED, JobStatus.COMPLETE])
    def test_generate_export_csv_invalid_status(self, caplog, status):
        export_job = factories.ExportJobFactory.create(status=status)
        generate_export_csv(str(export_job.id))

        self.assert_caplog_text(caplog, export_job.id)
        assert (
            "This job could not be started as it is either already running or completed."
            in caplog.text
        )

        export_job.refresh_from_db()
        assert export_job.status == JobStatus.FAILED

    def test_generate_export_csv_no_results(self, caplog):
        export_job = factories.ExportJobFactory.create()
        generate_export_csv(str(export_job.id))

        self.assert_caplog_text(caplog, export_job.id)
        assert (
            f"No results found for the export job with id {export_job.id}"
            in caplog.text
        )

        export_job.refresh_from_db()
        assert export_job.status == JobStatus.CANCELLED
        assert export_job.export_csv is None
        assert (
            f"No results found for the export job with id {export_job.id}. "
            f"Export job marked as CANCELLED."
        ) in caplog.text

    def test_generate_export_csv_exception(self, caplog):
        export_job = factories.ExportJobFactory.create()
        with patch(
            "backend.tasks.export_job_tasks.generate_export",
            side_effect=Exception("Mocked exception"),
        ):
            generate_export_csv(str(export_job.id))

        self.assert_caplog_text(caplog, export_job.id)
        assert (
            f"An error occurred while generating export for ExportJob id: {export_job.id}. "
            f"Error: Mocked exception."
        ) in caplog.text

        export_job.refresh_from_db()
        assert export_job.status == JobStatus.FAILED


@pytest.mark.django_db
class TestDeleteOldExportsTask(IgnoreTaskResultsMixin):
    TASK = delete_old_exports

    def get_valid_task_args(self):
        return None

    def get_export_job_with_csv(self):
        return factories.ExportJobFactory.create(
            export_csv=factories.FileFactory.create()
        )

    def test_no_exports_eligible_for_deletion(self, caplog):
        result = delete_old_exports.apply()
        assert result.state == "SUCCESS"

        assert (
            "No eligible export jobs found for deletion. No action taken."
            in caplog.text
        )
        assert ASYNC_TASK_START_TEMPLATE in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    def test_exports_eligible_for_deletion(self, caplog):
        export_job = self.get_export_job_with_csv()
        export_job.created = export_job.created - timedelta(days=8)
        export_job.save()

        result = delete_old_exports.apply()
        assert result.state == "SUCCESS"

        assert ExportJob.objects.count() == 0
        assert File.objects.count() == 0

        assert "Deleting 1 old export jobs and associated csv files." in caplog.text
        assert ASYNC_TASK_START_TEMPLATE in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    def test_delete_old_exports_error(self, caplog):
        export_job = self.get_export_job_with_csv()
        export_job.created = export_job.created - timedelta(days=8)
        export_job.save()

        with patch.object(
            ExportJob, "delete", side_effect=Exception("Mocked exception")
        ):
            result = delete_old_exports.apply()
            assert result.state == "FAILURE"

            assert "Error deleting old exports: Mocked exception" in caplog.text
            assert ASYNC_TASK_START_TEMPLATE in caplog.text
            assert ASYNC_TASK_END_TEMPLATE in caplog.text

    def test_delete_old_exports_invalid_fk(self, caplog):
        file = factories.FileFactory.create()
        export_job = factories.ExportJobFactory.create(export_csv=file)
        export_job.created = export_job.created - timedelta(days=8)
        export_job.save()

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM backend_file WHERE id = %s", [file.id])

        result = delete_old_exports.apply()
        assert result.state == "SUCCESS"
        assert ExportJob.objects.count() == 0
        assert File.objects.count() == 0
        assert "Deleting 1 old export jobs and associated csv files." in caplog.text
        assert (
            f"Missing export csv file for export job {export_job.id}. Skipping file deletion."
            in caplog.text
        )
