import pytest


@pytest.fixture(autouse=True)
def configure_settings(settings):
    # Celery tasks run synchronously for testing
    settings.CELERY_TASK_ALWAYS_EAGER = True
