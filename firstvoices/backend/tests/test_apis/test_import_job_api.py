import pytest

from backend.tests.test_apis.base.import_update_jobs.base_endpoints_test import (
    BaseImportUpdateEndpoints,
)


@pytest.mark.django_db
class TestImportEndpoints(BaseImportUpdateEndpoints):
    pass
