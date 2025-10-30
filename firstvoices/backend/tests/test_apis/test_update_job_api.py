import json

import pytest

from backend.models.constants import AppRole, Visibility
from backend.models.import_jobs import ImportJob, ImportJobMode
from backend.models.jobs import JobStatus
from backend.tests import factories
from backend.tests.test_apis.test_import_job_api import TestImportEndpoints
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestUpdateEndpoints(TestImportEndpoints):
    """
    End-to-end tests for the update-jobs API endpoints. Subclasses
    the base import-job tests for admin permissions and overrides methods as necessary.
    """

    API_LIST_VIEW = "api:updatejob-list"
    API_DETAIL_VIEW = "api:updatejob-detail"
    model = ImportJob

    def create_minimal_instance(self, site, visibility=None):
        return factories.ImportJobFactory.create(site=site, mode=ImportJobMode.UPDATE)

    def get_file_data(self, file):
        return {
            "path": f"http://testserver{file.content.url}",
            "mimetype": file.mimetype,
            "size": file.size,
        }

    def get_expected_response(self, instance, site):
        standard_fields = self.get_expected_entry_standard_fields(instance, site)
        return {
            **standard_fields,
            "runAsUser": instance.run_as_user,
            "data": self.get_file_data(instance.data),
            "mode": ImportJobMode.UPDATE.lower(),
            "taskId": instance.task_id,
            "status": instance.status,
            "message": instance.message,
            "validationTaskId": instance.task_id,
            "validationStatus": instance.validation_status,
            "validationReport": instance.validation_report,
            "failedRowsCsv": instance.failed_rows_csv,
        }

    def get_valid_data(self, site=None):
        return {
            "title": "Update Job",
            "data": get_sample_file("update_job/minimal.csv", "text/csv"),
            "mode": "update",
        }

    def get_valid_data_with_nulls(self, site=None):
        return self.get_valid_data(site=site)

    def get_valid_data_with_null_optional_charfields(self, site=None):
        # No optional char field
        pass

    def add_expected_defaults(self, data):
        return {
            **data,
        }

    def assert_created_instance(self, pk, data):
        instance = ImportJob.objects.get(pk=pk, mode=ImportJobMode.UPDATE)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        assert expected_data["mode"] == actual_response["mode"]
        assert actual_response["title"] == expected_data["title"]
        return self.assert_update_response(expected_data, actual_response)

    def assert_updated_instance(self, expected_data, actual_instance):
        assert expected_data["mode"] == actual_instance.mode
        assert expected_data["title"] == actual_instance.title
        expected_file_name = expected_data["data"].file.name.split("/")[-1]
        actual_file_name = actual_instance.data.content.file.name.split("/")[-1]
        assert expected_file_name == actual_file_name

    def assert_update_response(self, expected_data, actual_response):
        expected_file_name = expected_data["data"].file.name.split("/")[-1]
        actual_file_name = actual_response["data"]["path"].split("/")[-1]
        assert expected_file_name == actual_file_name

    @pytest.mark.skip(
        reason="Update job API does not have eligible optional charfields."
    )
    def test_create_with_null_optional_charfields_success_201(self):
        # Import job API does not have eligible optional charfields.
        pass

    @pytest.mark.skip(reason="Encodings tested in base import job tests.")
    def test_csv_with_valid_encodings_accepted(self, filename):
        # Encodings tested in base import job tests.
        pass

    def test_required_headers_missing(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file(
                "update_job/required_headers_missing.csv", "text/csv"
            ),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data["data"] == [
            "CSV file does not have the all the required headers. Required headers are ['id']"
        ]

    def test_duplicate_headers(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file("update_job/duplicate_cols.csv", "text/csv"),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data["data"] == [
            "CSV file contains duplicate headers: title,type."
        ]

    def test_failed_rows_csv_field_exists(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file(
                "update_job/invalid_dictionary_entry_updates.csv", "text/csv"
            ),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )
        response_data = json.loads(response.content)

        assert "failedRowsCsv" in response_data

    @pytest.mark.parametrize(
        "job_status", [JobStatus.ACCEPTED, JobStatus.COMPLETE, JobStatus.STARTED]
    )
    def test_cannot_delete_successful_job(self, job_status):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.SUPERADMIN
        )
        job = factories.ImportJobFactory.create(site=site, mode=ImportJobMode.UPDATE)
        job.status = job_status
        job.save()

        response = self.client.delete(
            self.get_detail_endpoint(key=self.get_lookup_key(job), site_slug=site.slug)
        )

        assert response.status_code == 400

        jobs = ImportJob.objects.filter(id=job.id)
        assert jobs.count() == 1

    @pytest.mark.parametrize("job_status", [JobStatus.ACCEPTED, JobStatus.STARTED])
    def test_cannot_delete_job_with_started_validation(self, job_status):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.SUPERADMIN
        )
        job = factories.ImportJobFactory.create(site=site, mode=ImportJobMode.UPDATE)
        job.validation_status = job_status
        job.save()

        response = self.client.delete(
            self.get_detail_endpoint(key=self.get_lookup_key(job), site_slug=site.slug)
        )

        assert response.status_code == 400

        jobs = ImportJob.objects.filter(id=job.id)
        assert jobs.count() == 1

    def test_update_job_list_only_update_jobs(self):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.SUPERADMIN
        )
        update_job = factories.ImportJobFactory.create(
            site=site, mode=ImportJobMode.UPDATE
        )
        import_job = factories.ImportJobFactory.create(
            site=site, mode=ImportJobMode.SKIP_DUPLICATES
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 1

        returned_job_ids = [item["id"] for item in response_data["results"]]

        assert str(update_job.id) in returned_job_ids
        assert str(import_job.id) not in returned_job_ids
