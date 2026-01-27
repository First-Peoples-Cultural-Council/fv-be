import pytest

from backend.models.jobs import ExportJob
from backend.tests import factories
from backend.tests.test_apis.base.base_async_api_test import (
    AsyncWorkflowTestMixin,
    BaseAsyncSiteContentApiTest,
)


class TestExportJobAPI(
    AsyncWorkflowTestMixin,
    BaseAsyncSiteContentApiTest,
):
    API_LIST_VIEW = "api:exportjob-list"
    API_DETAIL_VIEW = "api:exportjob-detail"

    model = ExportJob

    @pytest.fixture(scope="function")
    def mock_dictionary_cleanup_task(self, mocker):
        self.mocked_func = mocker.patch(
            "backend.tasks.dictionary_cleanup_tasks.cleanup_dictionary.apply_async"
        )

    def create_minimal_instance(self, site, visibility):
        return factories.ExportJobFactory.create(site=site)

    def get_file_data(self, file):
        return {
            "path": f"http://testserver{file.content.url}",
            "mimetype": file.mimetype,
            "size": file.size,
        }

    def get_expected_detail_response(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "taskId": instance.task_id,
            "status": instance.status,
            "message": instance.message,
            "exportCsv": instance.export_csv,
        }

    def get_expected_response(self, instance, site):
        return self.get_expected_detail_response(instance, site)

    def get_valid_data(self, site=None):
        return {"site": str(site.id)}

    def assert_created_instance(self, pk, data):
        instance = ExportJob.objects.get(pk=pk)
        return self.get_expected_response(instance, instance.site)

    def assert_created_response(self, expected_data, actual_response):
        site_id = expected_data["site"]
        pk = actual_response["id"]
        job = self.model.objects.get(site=site_id, pk=pk)
        assert actual_response == self.get_expected_response(job, job.site)

    @pytest.mark.skip(reason="Export jobs have no eligible nulls.")
    def test_create_with_nulls_success_201(self):
        pass

    @pytest.mark.skip(reason="Export jobs require no data to post.")
    def test_create_invalid_400(self):
        pass

    @pytest.mark.skip(reason="Export jobs have no eligible optional charfields.")
    def test_create_with_null_optional_charfields_success_201(self):
        pass

    @pytest.mark.skip(reason="Export jobs have no eligible optional charfields.")
    def test_update_with_null_optional_charfields_success_200(self):
        pass

    @pytest.mark.skip(reason="Export jobs can be deleted.")
    def test_cannot_delete_successful_job(self):
        pass
