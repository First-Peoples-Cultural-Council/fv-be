from backend.tests import factories

from .base_media_test import BaseMediaApiTest


class TestVideosEndpoint(BaseMediaApiTest):
    """
    End-to-end tests that the videos endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:video-list"
    API_DETAIL_VIEW = "api:video-detail"
    sample_filename = "video_example_small.mp4"
    sample_filetype = "video/mp4"

    def create_minimal_instance(self, site, visibility):
        return factories.VideoFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return self.get_expected_video_data(instance)
