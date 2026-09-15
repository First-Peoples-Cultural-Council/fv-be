from unittest import mock

import pytest


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
