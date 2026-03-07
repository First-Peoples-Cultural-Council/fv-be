import json

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.models.jobs import ExportJob, JobStatus
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
            "exportParams": instance.export_params,
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
        expected_response = self.get_expected_response(job, job.site)

        assert actual_response["taskId"] == expected_response["taskId"]
        assert actual_response["status"] == expected_response["status"]
        assert actual_response["message"] == expected_response["message"]
        assert actual_response["exportCsv"] == expected_response["exportCsv"]

    @pytest.mark.skip(reason="Export jobs have no eligible nulls.")
    def test_create_with_nulls_success_201(self):
        # Export jobs have no eligible nulls.
        pass

    @pytest.mark.skip(reason="Export jobs require no data to post.")
    def test_create_invalid_400(self):
        # Export jobs require no data to post.
        pass

    @pytest.mark.skip(reason="Export jobs have no eligible optional charfields.")
    def test_create_with_null_optional_charfields_success_201(self):
        # Export jobs have no eligible optional charfields.
        pass

    @pytest.mark.skip(reason="Export jobs have no eligible optional charfields.")
    def test_update_with_null_optional_charfields_success_200(self):
        # Export jobs have no eligible optional charfields.
        pass

    @pytest.mark.skip(reason="Export jobs can be deleted after completion.")
    def test_cannot_delete_successful_job(self, job_status):
        # Export jobs can be deleted after completion.
        pass

    @pytest.mark.django_db
    @pytest.mark.parametrize("job_status", [JobStatus.ACCEPTED, JobStatus.STARTED])
    def test_cannot_delete_in_progress_job(self, job_status):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.SUPERADMIN
        )
        job = factories.ExportJobFactory.create(site=site)
        job.status = job_status
        job.save()

        response = self.client.delete(
            self.get_detail_endpoint(key=self.get_lookup_key(job), site_slug=site.slug)
        )

        assert response.status_code == 400

        jobs = ExportJob.objects.filter(id=job.id)
        assert jobs.count() == 1

    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_create_201_language_team(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json"
        )

        assert response.status_code == 201

    @pytest.mark.django_db
    def test_export_job_accepted(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )

        post_response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json"
        )

        assert post_response.status_code == 201
        post_response_data = json.loads(post_response.content)

        response = self.client.get(
            self.get_detail_endpoint(key=post_response_data["id"], site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["status"] == JobStatus.ACCEPTED

    @pytest.mark.django_db
    def test_export_job_limit_per_user(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )

        for _ in range(10):
            response = self.client.post(
                self.get_list_endpoint(site_slug=site.slug), format="json"
            )
            assert response.status_code == 201

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json"
        )
        assert response.status_code == 400
        assert (
            response.json()["nonFieldErrors"][0]
            == "You have reached the maximum number of simultaneous export jobs (10). "
            "Please delete completed jobs that you no longer need to allow new export jobs to be created."
        )
