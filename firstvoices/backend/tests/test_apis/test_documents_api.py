import json

import pytest

from backend.models.constants import Visibility
from backend.models.media import Document
from backend.tests import factories
from backend.tests.test_apis.base_media_test import BaseMediaApiTest


class TestDocumentEndpoint(BaseMediaApiTest):
    """
    End-to-end tests that the documents endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:document-list"
    API_DETAIL_VIEW = "api:document-detail"
    sample_filename = "sample-document.pdf"
    sample_filetype = "application/pdf"
    model = Document
    model_factory = factories.DocumentFactory
    content_type_json = "application/json"

    def get_expected_response(self, instance, site, detail_view=False):
        return self.get_expected_document_data(instance)

    @pytest.mark.django_db
    def test_detail(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=None)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == self.get_expected_document_data(instance)

    def assert_created_response(
        self, expected_data, actual_response, detail_view=False
    ):
        instance = Document.objects.get(pk=actual_response["id"])
        assert actual_response == self.get_expected_document_data(instance)

    @pytest.mark.django_db
    def test_create(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

    def assert_update_response_document(
        self, original_instance, expected_data, actual_response
    ):
        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data={**expected_data},
        )

    def assert_patch_file_original_fields(self, original_instance, updated_instance):
        self.assert_original_secondary_fields(original_instance, updated_instance)
        assert updated_instance.title == original_instance.title

    def assert_patch_file_updated_fields(self, data, updated_instance):
        assert data["original"].name in updated_instance.original.content.path
