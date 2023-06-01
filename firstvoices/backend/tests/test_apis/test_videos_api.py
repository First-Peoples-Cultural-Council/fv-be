from backend.tests import factories

from .base_api_test import BaseReadOnlyUncontrolledSiteContentApiTest
from .base_media_test import MediaTestMixin


class TestVideosEndpoint(MediaTestMixin, BaseReadOnlyUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the videos endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:video-list"
    API_DETAIL_VIEW = "api:video-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.VideoFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return self.get_expected_video_data(instance)
