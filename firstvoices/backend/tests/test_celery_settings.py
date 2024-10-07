import pytest

from firstvoices import settings


class TestCelerySettings:
    @pytest.mark.django_db
    def test_task_ignore_result(self):
        assert getattr(settings, "CELERY_TASK_IGNORE_RESULT", False) is True
