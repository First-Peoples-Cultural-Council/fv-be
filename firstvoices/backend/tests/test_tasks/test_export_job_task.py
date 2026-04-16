from datetime import timedelta
from unittest.mock import patch

import pytest

from backend.models.files import File
from backend.models.jobs import ExportJob
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE
from backend.tasks.export_job_tasks import delete_old_exports
from backend.tests import factories


@pytest.mark.django_db
class TestDeleteOldExportsTask:
    TASK = delete_old_exports

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
