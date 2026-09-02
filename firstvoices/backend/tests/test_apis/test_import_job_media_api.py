import pytest

from backend.tests.test_apis.base.import_update_jobs.base_media_endpoint_test import (
    BaseImportUpdateJobMediaEndpoint,
)


@pytest.mark.django_db
class TestImportJobMediaEndpoint(BaseImportUpdateJobMediaEndpoint):
    pass
