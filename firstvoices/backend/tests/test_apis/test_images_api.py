from backend.tests import factories

from .base_api_test import BaseReadOnlyUncontrolledSiteContentApiTest
from .base_media_test import MediaTestMixin


class TestImagesEndpoint(MediaTestMixin, BaseReadOnlyUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the images endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:image-list"
    API_DETAIL_VIEW = "api:image-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.ImageFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return self.get_expected_image_data(instance)
