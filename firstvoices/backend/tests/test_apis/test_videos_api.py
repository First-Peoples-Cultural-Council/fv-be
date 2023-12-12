import json

import pytest

from backend.models.media import ImageFile, Video, VideoFile
from backend.tests import factories

from ...models.constants import Visibility
from .base_media_test import BaseMediaApiTest


class TestVideosEndpoint(BaseMediaApiTest):
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
            is_shared=True,
        )
        video.save()
        return video

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

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        self.assert_original_secondary_fields(original_instance, updated_instance)
        assert updated_instance.original.id == original_instance.original.id

    def assert_original_secondary_fields(self, original_instance, updated_instance):
        # everything but title
        self.assert_secondary_fields(
            expected_data={
                "description": original_instance.description,
                "acknowledgement": original_instance.acknowledgement,
                "excludeFromKids": original_instance.exclude_from_kids,
                "excludeFromGames": original_instance.exclude_from_games,
                "isShared": original_instance.is_shared,
            },
            updated_instance=updated_instance,
        )

    def assert_secondary_fields(self, expected_data, updated_instance):
        assert updated_instance.description == expected_data["description"]
        assert updated_instance.acknowledgement == expected_data["acknowledgement"]
        assert updated_instance.exclude_from_kids == expected_data["excludeFromKids"]
        assert updated_instance.exclude_from_games == expected_data["excludeFromGames"]
        assert updated_instance.is_shared == expected_data["isShared"]

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        assert updated_instance.title == data["title"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        self.assert_response(
            actual_response=actual_response,
            expected_data={
                "id": str(original_instance.id),
                "title": data["title"],
                "description": original_instance.description,
                "acknowledgement": original_instance.acknowledgement,
                "excludeFromKids": original_instance.exclude_from_kids,
                "excludeFromGames": original_instance.exclude_from_games,
                "isShared": original_instance.is_shared,
                "original": original_instance.original,
            },
        )

    def assert_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["description"] == expected_data["description"]
        assert actual_response["acknowledgement"] == expected_data["acknowledgement"]
        assert actual_response["excludeFromKids"] == expected_data["excludeFromKids"]
        assert actual_response["excludeFromGames"] == expected_data["excludeFromGames"]
        assert actual_response["isShared"] == expected_data["isShared"]

        expected_file_path = (
            expected_data["original"].content.url
            if hasattr(expected_data["original"], "content")
            else expected_data["original"].name
        )
        # Split the filename and extension from the file paths and check for each to avoid async tests appending
        # characters to the end of the filename when file path already exists.
        expected_filename = expected_file_path.split(".")[0]
        expected_file_extension = expected_file_path.split(".")[1]
        actual_filename = actual_response["original"]["path"].split(".")[0]
        actual_file_extension = actual_response["original"]["path"].split(".")[1]
        assert expected_filename in actual_filename
        assert expected_file_extension in actual_file_extension

    def assert_updated_instance(self, expected_data, actual_instance):
        self.assert_secondary_fields(expected_data, actual_instance)
        assert actual_instance.title == expected_data["title"]

    def assert_update_response(self, expected_data, actual_response):
        self.assert_response(
            actual_response=actual_response,
            expected_data={**expected_data},
        )

    @pytest.mark.django_db
    def test_patch_file_success_200(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_original_instance_for_patch(site=site)
        data = self.get_valid_patch_file_data(site)

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

        self.assert_patch_file_original_fields(
            instance, self.get_updated_patch_instance(instance)
        )
        self.assert_patch_file_updated_fields(
            data, self.get_updated_patch_instance(instance)
        )
        self.assert_update_patch_file_response(instance, data, response_data)

    def assert_patch_file_original_fields(self, original_instance, updated_instance):
        self.assert_original_secondary_fields(original_instance, updated_instance)
        assert updated_instance.title == original_instance.title

    def assert_patch_file_updated_fields(self, data, updated_instance):
        assert data["original"].name in updated_instance.original.content.path

    def assert_update_patch_file_response(
        self, original_instance, data, actual_response
    ):
        self.assert_response(
            actual_response=actual_response,
            expected_data={
                "id": str(original_instance.id),
                "title": original_instance.title,
                "description": original_instance.description,
                "acknowledgement": original_instance.acknowledgement,
                "excludeFromKids": original_instance.exclude_from_kids,
                "excludeFromGames": original_instance.exclude_from_games,
                "isShared": original_instance.is_shared,
                "original": data["original"],
            },
        )

    def assert_patch_speaker_original_fields(self, original_instance, updated_instance):
        self.assert_original_secondary_fields(original_instance, updated_instance)
        assert updated_instance.title == original_instance.title
        assert updated_instance.original.id == original_instance.original.id

    @pytest.fixture()
    def disable_celery(self, settings):
        # Sets the celery tasks to run synchronously for testing
        settings.CELERY_TASK_ALWAYS_EAGER = True

    @pytest.mark.disable_thumbnail_mocks
    @pytest.mark.django_db
    def test_patch_old_thumbnail_deleted(self, disable_celery):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = factories.VideoFactory.create(site=site)
        instance = Video.objects.get(pk=instance.id)
        data = self.get_valid_patch_file_data(site)

        assert VideoFile.objects.count() == 1
        assert ImageFile.objects.count() == 3
        old_original_file_id = instance.original.id
        old_thumbnail_id = instance.thumbnail.id
        old_medium_id = instance.medium.id
        old_small_id = instance.small.id

        assert VideoFile.objects.filter(id=old_original_file_id).exists()
        assert ImageFile.objects.filter(id=old_thumbnail_id).exists()
        assert ImageFile.objects.filter(id=old_medium_id).exists()
        assert ImageFile.objects.filter(id=old_small_id).exists()

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
        assert ImageFile.objects.count() == 3
        assert not VideoFile.objects.filter(id=old_original_file_id).exists()
        assert not ImageFile.objects.filter(id=old_thumbnail_id).exists()
        assert not ImageFile.objects.filter(id=old_medium_id).exists()
        assert not ImageFile.objects.filter(id=old_small_id).exists()
