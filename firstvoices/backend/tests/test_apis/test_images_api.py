import json

import pytest

from backend.models.media import Image, ImageFile
from backend.tests import factories

from ...models.constants import Visibility
from .base_media_test import BaseVisualMediaAPITest


class TestImagesEndpoint(BaseVisualMediaAPITest):
    """
    End-to-end tests that the images endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:image-list"
    API_DETAIL_VIEW = "api:image-detail"
    sample_filename = "sample-image.jpg"
    sample_filetype = "image/jpg"
    model = Image

    def create_minimal_instance(self, site, visibility):
        return factories.ImageFactory.create(site=site)

    def create_original_instance_for_patch(self, site):
        image = factories.ImageFactory.create(
            site=site,
            title="Original title",
            description="Original description",
            acknowledgement="Original ack",
            exclude_from_kids=True,
            exclude_from_games=True,
        )
        image.save()
        return image

    def get_expected_response(self, instance, site):
        return self.get_expected_image_data(instance)

    def assert_created_response(self, expected_data, actual_response):
        instance = Image.objects.get(pk=actual_response["id"])
        expected = self.get_expected_image_data(instance)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in actual_response:
                actual_response.pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert actual_response == expected

    @pytest.mark.disable_thumbnail_mocks
    @pytest.mark.django_db
    def test_patch_old_file_deleted(self, disable_celery):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = factories.ImageFactory.create(site=site)
        instance = Image.objects.get(pk=instance.id)
        data = self.get_valid_patch_file_data(site)

        assert ImageFile.objects.count() == 4
        old_original_file_id = instance.original.id

        assert ImageFile.objects.filter(id=old_original_file_id).exists()

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(instance.id)

        # Check that old files have been deleted
        assert ImageFile.objects.count() == 4
        assert not ImageFile.objects.filter(id=old_original_file_id).exists()
