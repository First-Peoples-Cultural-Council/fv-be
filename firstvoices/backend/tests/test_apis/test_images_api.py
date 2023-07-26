from backend.models.media import Image
from backend.tests import factories

from .base_media_test import BaseMediaApiTest


class TestImagesEndpoint(BaseMediaApiTest):
    """
    End-to-end tests that the images endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:image-list"
    API_DETAIL_VIEW = "api:image-detail"
    model = Image

    def create_minimal_instance(self, site, visibility):
        return factories.ImageFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return self.get_expected_image_data(instance)

    def assert_created_response(self, expected_data, actual_response):
        instance = Image.objects.get(pk=actual_response["id"])
        assert actual_response == self.get_expected_image_data(instance)
