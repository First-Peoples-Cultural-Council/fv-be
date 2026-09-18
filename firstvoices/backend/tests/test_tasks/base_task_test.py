from unittest import mock

import pytest

from backend.models.import_jobs import ImportJobStatus
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class IgnoreTaskResultsMixin:
    """Test mixin for tasks that ignore Celery results."""

    TASK = None

    def get_valid_task_args(self):
        raise NotImplementedError()

    def test_task_ignore_result_set(self):
        assert self.TASK.ignore_result is True

    @mock.patch("celery.backends.base.BaseBackend.store_result")
    def test_task_does_not_store_result(self, mock_store_result):
        task_args = self.get_valid_task_args()

        self.TASK.apply_async(
            args=task_args,
        )
        mock_store_result.assert_not_called()


@pytest.mark.django_db
class IgnoreTaskResultsImportMixin(IgnoreTaskResultsMixin):
    def get_import_job(
        self,
        file,
        status=ImportJobStatus.ACCEPTED,
        validation_status=ImportJobStatus.COMPLETE,
    ):
        self.import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            status=status,
            validation_status=validation_status,
        )
        return self.import_job

    def get_valid_task_args(self):
        if not hasattr(self, "import_job"):
            file_content = get_sample_file(
                file_dir=self.CSV_FILES_DIR,
                filename="minimal.csv",
                mimetype=self.MIMETYPE,
            )
            file = factories.FileFactory(content=file_content)
            self.import_job = self.get_import_job(file=file)

        return (str(self.import_job.id),)
