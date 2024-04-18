import json
import os
import sys

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile

from backend.models.constants import Visibility
from backend.models.import_jobs import ImportJob
from backend.tests.factories.import_job_factories import ImportJobFactory
from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    WriteApiTestMixin,
)
from backend.tests.test_apis.base_media_test import FormDataMixin


class TestImportEndpoints(
    FormDataMixin,
    WriteApiTestMixin,
    SiteContentCreateApiTestMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    """
    End-to-end tests that the /import endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:importjob-list"
    API_DETAIL_VIEW = "api:importjob-detail"
    model = ImportJob

    def get_sample_file(self, filename, mimetype="text/csv"):
        path = (
            os.path.dirname(os.path.realpath(__file__))
            + f"/../factories/resources/{filename}"
        )
        file = open(path, "rb")
        return InMemoryUploadedFile(
            file,
            "FileField",
            filename,
            mimetype,
            sys.getsizeof(file),
            None,
        )

    def create_minimal_instance(self, site, visibility=None):
        return ImportJobFactory.create(site=site)

    def get_file_data(self, file):
        return {
            "path": f"http://testserver{file.content.url}",
            "mimetype": file.mimetype,
            "size": file.size,
        }

    def get_expected_response(self, instance, site):
        return {
            "id": str(instance.id),
            "url": f"http://testserver{self.get_detail_endpoint(instance.id, instance.site.slug)}",
            "description": instance.description,
            "runAsUser": instance.run_as_user,
            "data": self.get_file_data(instance.data),
        }

    def get_valid_data(self, site=None):
        return {
            "description": "Test Description",
            "data": self.get_sample_file("import_job_minimal.csv"),
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "data": self.get_sample_file("import_job_minimal.csv"),
        }

    def add_expected_defaults(self, data):
        return {
            **data,
        }

    def assert_created_instance(self, pk, data):
        instance = ImportJob.objects.get(pk=pk)
        if "description" in data:
            assert instance.description == data["description"]
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        # To handle create_with_nulls_success_201
        if "description" in expected_data and "description" in actual_response:
            assert actual_response["description"] == expected_data["description"]
        return self.assert_update_response(expected_data, actual_response)

    def assert_updated_instance(self, expected_data, actual_instance):
        # Verifying file
        expected_file_name = expected_data["data"].file.name.split("/")[-1]
        actual_file_name = actual_instance.data.content.file.name.split("/")[-1]
        assert expected_file_name == actual_file_name

    def assert_update_response(self, expected_data, actual_response):
        # Verifying file
        expected_file_name = expected_data["data"].file.name.split("/")[-1]
        actual_file_name = actual_response["data"]["path"].split("/")[-1]
        assert expected_file_name == actual_file_name

    @pytest.mark.skip("This endpoint has custom permissions")
    def test_detail_team_access(self, role):
        # Only editor or above have access to this object
        pass

    @pytest.mark.skip("This endpoint has custom permissions")
    def test_detail_member_access(self, role):
        # Only editor or above have access to this object
        pass

    @pytest.mark.django_db
    def test_invalid_dimensions(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "description": "Test Description",
            "data": self.get_sample_file("import_job_invalid_dimensions.csv"),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data["data"] == [
            "CSV file has invalid dimensions. The size of a column or row doesn't fit the table dimensions."
        ]

    @pytest.mark.django_db
    def test_required_headers_missing(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "description": "Test Description",
            "data": self.get_sample_file("import_job_missing_req_headers.csv"),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data["data"] == [
            "CSV file does not have the required headers. Please check and upload again."
        ]
