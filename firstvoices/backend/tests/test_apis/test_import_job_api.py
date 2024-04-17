import json
import os
import sys

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile

from backend.models.constants import Visibility
from backend.models.import_jobs import ImportJob
from backend.tests.factories.import_job_factories import ImportJobFactory
from backend.tests.test_apis.base_api_test import BaseUncontrolledSiteContentApiTest
from backend.tests.test_apis.base_media_test import FormDataMixin


class TestImportEndpoints(FormDataMixin, BaseUncontrolledSiteContentApiTest):
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

    def get_expected_response(self, instance, site):
        return {
            "id": str(instance.id),
            "url": f"http://testserver{self.get_detail_endpoint(instance.id, instance.site.slug)}",
            "description": instance.description,
            "runAsUser": instance.run_as_user,
            "data": {
                "path": f"http://testserver/{instance.data.content}",
                "mimetype": instance.data.mimetype,
                "size": instance.data.size,
            },
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
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass

    @pytest.mark.skip("The endpoint does not support PATCH requests atm.")
    @pytest.mark.django_db
    def test_patch_403(self):
        pass

    @pytest.mark.skip("The endpoint does not support PATCH requests atm.")
    @pytest.mark.django_db
    def test_patch_site_missing_404(self):
        pass

    @pytest.mark.skip("The endpoint does not support PATCH requests atm.")
    @pytest.mark.django_db
    def test_patch_invalid_400(self):
        pass

    @pytest.mark.skip("The endpoint does not support PATCH requests atm.")
    @pytest.mark.django_db
    def test_patch_instance_missing_404(self):
        pass

    @pytest.mark.skip("The endpoint does not support PATCH requests atm.")
    @pytest.mark.django_db
    def test_patch_success_200(self):
        pass

    @pytest.mark.skip("The endpoint does not support PUT requests atm.")
    @pytest.mark.django_db
    def test_update_invalid_400(self):
        pass

    @pytest.mark.skip("The endpoint does not support PUT requests atm.")
    @pytest.mark.django_db
    def test_update_403(self):
        pass

    @pytest.mark.skip("The endpoint does not support PUT requests atm.")
    @pytest.mark.django_db
    def test_update_site_missing_404(self):
        pass

    @pytest.mark.skip("The endpoint does not support PUT requests atm.")
    @pytest.mark.django_db
    def test_update_instance_missing_404(self):
        pass

    @pytest.mark.skip("The endpoint does not support PUT requests atm.")
    @pytest.mark.django_db
    def test_update_success_200(self):
        pass

    @pytest.mark.skip("The endpoint does not support PUT requests atm.")
    @pytest.mark.django_db
    def test_update_with_nulls_success_200(self):
        pass

    @pytest.mark.skip("This endpoint has custom permissions")
    def test_detail_team_access(self, role):
        pass

    @pytest.mark.skip("This endpoint has custom permissions")
    def test_detail_member_access(self, role):
        # See custom permission tests instead
        pass

    def assert_updated_instance(self, expected_data, actual_instance):
        pass

    def assert_update_response(self, expected_data, actual_response):
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
