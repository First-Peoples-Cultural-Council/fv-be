from backend.models.media import Video
from backend.tests import factories

from .base_media_test import BaseMediaApiTest


class TestVideosEndpoint(BaseMediaApiTest):
    """
    End-to-end tests that the videos endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:video-list"
    API_DETAIL_VIEW = "api:video-detail"
    sample_filename = "video_example.mp4"
    sample_filetype = "video/mp4"
    model = Video

    def create_minimal_instance(self, site, visibility):
        return factories.VideoFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return self.get_expected_video_data(instance)

    def assert_created_response(self, expected_data, actual_response):
        instance = Video.objects.get(pk=actual_response["id"])
        expected = self.get_expected_video_data(instance)

        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in actual_response:
                actual_response.pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert actual_response == expected
