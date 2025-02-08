import json

import pytest

from backend.models.constants import Visibility
from backend.models.media import Video
from backend.tests import factories

from .base_media_test import BaseVisualMediaAPITest


class TestVideosEndpoint(BaseVisualMediaAPITest):
    """
    End-to-end tests that the videos endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:video-list"
    API_DETAIL_VIEW = "api:video-detail"
    sample_filename = "video_example_small.mp4"
    sample_filetype = "video/mp4"
    model = Video
    model_factory = factories.VideoFactory
    related_key = "related_videos"

    def get_expected_response(self, instance, site, detail_view=False):
        return self.get_expected_video_data(instance, detail_view)

    def assert_created_response(
        self, expected_data, actual_response, detail_view=False
    ):
        instance = Video.objects.get(pk=actual_response["id"])
        expected = self.get_expected_video_data(instance, detail_view)

        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in actual_response:
                actual_response.pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert actual_response == expected

    @pytest.mark.django_db
    def test_usages_field_extra_fields(self):
        expected_data = self.add_related_media_to_objects(visibility=Visibility.PUBLIC)

        custom_page = factories.SitePageFactory(
            site=expected_data["site"], banner_video=expected_data["media_instance"]
        )

        response = self.client.get(
            self.get_detail_endpoint(
                key=expected_data["media_instance"].id,
                site_slug=expected_data["site"].slug,
            )
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        custom_pages = response_data["usage"]["customPages"]
        assert len(custom_pages) == 1
        assert custom_pages[0]["id"] == str(custom_page.id)

        assert response_data["usage"]["total"] == expected_data["total"] + 1

    @pytest.mark.django_db
    def test_usages_field_permissions_extra_fields(self):
        expected_data = self.add_related_media_to_objects(visibility=Visibility.TEAM)

        factories.SitePageFactory(
            site=expected_data["site"],
            banner_video=expected_data["media_instance"],
            visibility=Visibility.TEAM,
        )

        response = self.client.get(
            self.get_detail_endpoint(
                key=expected_data["media_instance"].id,
                site_slug=expected_data["site"].slug,
            )
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["usage"]["customPages"]) == 0
