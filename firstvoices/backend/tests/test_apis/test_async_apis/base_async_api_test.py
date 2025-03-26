from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SuperAdminAsyncJobPermissionsMixin,
    WriteApiTestMixin,
)


class BaseAsyncApiTest(
    SuperAdminAsyncJobPermissionsMixin,
    SiteContentCreateApiTestMixin,
    WriteApiTestMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    """
    Basic tests for APIs that queue asynchronous jobs. This includes:
    - Read and Create tests for uncontrolled site content models
    - Tests that only superadmins can read and create
    - Tests standard workflow rules for queuing, starting, cancelling, and deleting jobs
    """

    def test_create_first_job(self):
        pass

    def test_create_nothing_running(self):
        pass

    def test_create_already_queued(self):
        pass

    def test_create_already_running(self):
        pass

    def test_delete_success(self):
        pass

    def test_delete_after_started(self):
        pass
