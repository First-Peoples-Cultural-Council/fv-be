from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from backend.models import JoinRequest
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE
from backend.tasks.join_request_tasks import delete_old_join_requests
from backend.tests import factories
from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin


@pytest.mark.django_db
class TestDeleteOldJoinRequestsTask(IgnoreTaskResultsMixin):
    TASK = delete_old_join_requests

    def get_valid_task_args(self):
        return None

    def test_no_join_requests_eligible_for_deletion(self, caplog):
        result = delete_old_join_requests.apply()

        assert result.state == "SUCCESS"
        assert (
            "No eligible join requests found for deletion. No action taken."
            in caplog.text
        )
        assert ASYNC_TASK_START_TEMPLATE in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    def test_deletes_join_requests_older_than_30_days(self, caplog):
        join_request = factories.JoinRequestFactory.create()
        factories.JoinRequestReasonFactory.create(join_request=join_request)
        join_request.created = timezone.now() - timedelta(days=31)
        join_request.save()

        result = delete_old_join_requests.apply()

        assert result.state == "SUCCESS"
        assert JoinRequest.objects.count() == 0
        assert "Deleting 1 old join requests." in caplog.text
        assert ASYNC_TASK_START_TEMPLATE in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    def test_keeps_join_requests_created_within_30_days(self):
        join_request = factories.JoinRequestFactory.create()

        result = delete_old_join_requests.apply()

        assert result.state == "SUCCESS"
        assert JoinRequest.objects.filter(id=join_request.id).exists()

    def test_delete_old_join_requests_error(self, caplog):
        join_request = factories.JoinRequestFactory.create()
        join_request.created = timezone.now() - timedelta(days=31)
        join_request.save()

        with patch.object(
            JoinRequest, "delete", side_effect=Exception("Mocked exception")
        ):
            result = delete_old_join_requests.apply()

        assert result.state == "FAILURE"
        assert "Error deleting old join requests: Mocked exception" in caplog.text
        assert ASYNC_TASK_START_TEMPLATE in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text
