from datetime import timedelta

import pytest

from backend.models.files import File
from backend.models.jobs import ExportJob
from backend.tasks.export_job_tasks import delete_old_exports
from backend.tests import factories


@pytest.mark.django_db
class TestDeleteOldExportsTask:
    TASK = delete_old_exports

    def get_export_job_with_csv(self):
        return factories.ExportJobFactory.create(
            export_csv=factories.FileFactory.create()
        )

    def test_no_exports_eligible_for_deletion(self):
        result = delete_old_exports.apply()
        assert result.state == "SUCCESS"

    def test_exports_eligible_for_deletion(self):
        export_job = self.get_export_job_with_csv()
        export_job.created = export_job.created - timedelta(days=8)
        export_job.save()

        result = delete_old_exports.apply()
        assert result.state == "SUCCESS"

        assert ExportJob.objects.count() == 0
        assert File.objects.count() == 0
