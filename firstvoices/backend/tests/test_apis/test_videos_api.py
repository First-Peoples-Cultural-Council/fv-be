import json

import pytest

from backend.models.media import Video, VideoFile
from backend.tests import factories

from ...models.constants import Visibility
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

    def create_minimal_instance(self, site, visibility):
        return factories.VideoFactory.create(site=site)

    def create_original_instance_for_patch(self, site):
        video = factories.VideoFactory.create(
            site=site,
            title="Original title",
            description="Original description",
            acknowledgement="Original ack",
            exclude_from_kids=True,
            exclude_from_games=True,
        )
        video.save()
        return video

    def get_expected_response(self, instance, site, detail_view):
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

    @pytest.mark.disable_thumbnail_mocks
    @pytest.mark.django_db
    def test_patch_old_file_deleted(self, disable_celery):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = factories.VideoFactory.create(site=site)
        instance = Video.objects.get(pk=instance.id)
        data = self.get_valid_patch_file_data(site)

        assert VideoFile.objects.count() == 1
        old_original_file_id = instance.original.id

        assert VideoFile.objects.filter(id=old_original_file_id).exists()

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
        assert VideoFile.objects.count() == 1
        assert not VideoFile.objects.filter(id=old_original_file_id).exists()

    def add_related_media_to_objects(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site, visibility=Visibility.PUBLIC)

        character = factories.CharacterFactory(site=site, title="a", sort_order=1)
        character.related_videos.add(instance)

        dict_entry = factories.DictionaryEntryFactory(site=site)
        dict_entry.related_videos.add(instance)

        song = factories.SongFactory(site=site)
        song.related_videos.add(instance)

        story_1 = factories.StoryFactory(site=site)
        story_1.related_videos.add(instance)

        story_page_1 = factories.StoryPageFactory(site=site, story=story_1)
        story_page_1.related_videos.add(instance)

        story_2 = factories.StoryFactory(site=site)
        story_page_2 = factories.StoryPageFactory(site=site, story=story_2)
        story_page_2.related_videos.add(instance)

        total = 5

        return {
            "site": site,
            "media_instance": instance,
            "character": character,
            "dict_entry": dict_entry,
            "song": song,
            "stories": [story_1, story_2],
            "total": total,
        }

    @pytest.mark.django_db
    def test_usages_field_extra_fields(self):
        expected_data = self.add_related_media_to_objects()

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
