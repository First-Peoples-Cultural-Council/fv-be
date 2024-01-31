import json
import os
import sys

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test.client import encode_multipart
from rest_framework.reverse import reverse

from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis import base_api_test

VIMEO_VIDEO_LINK = "https://vimeo.com/226053498"
YOUTUBE_VIDEO_LINK = "https://www.youtube.com/watch?v=abc123"
MOCK_EMBED_LINK = "https://mock_embed_link.com/"
MOCK_THUMBNAIL_LINK = "https://mock_thumbnail_link.com/"


class FormDataMixin:
    content_type = "multipart/form-data; boundary=TestBoundaryString"
    boundary_string = "TestBoundaryString"

    def format_upload_data(self, data):
        """Encode multipart form data instead of json"""
        return encode_multipart(self.boundary_string, data)


class MediaTestMixin:
    """
    Utilities for testing media APIs
    """

    def get_sample_file(self, filename, mimetype, title=None):
        path = (
            os.path.dirname(os.path.realpath(__file__))
            + f"/../factories/resources/{filename}"
        )
        file = open(path, "rb")
        return InMemoryUploadedFile(
            file,
            "FileField",
            title if title is not None else filename,
            mimetype,
            sys.getsizeof(file),
            None,
        )

    def get_basic_media_data(self, instance, view_name, detail_view):
        url = reverse(
            view_name, current_app=self.APP_NAME, args=[instance.site.slug, instance.id]
        )

        data = {
            "id": str(instance.id),
            "url": f"http://testserver{url}",
            "title": instance.title,
            "description": instance.description,
            "acknowledgement": instance.acknowledgement,
            "excludeFromGames": instance.exclude_from_games,
            "excludeFromKids": instance.exclude_from_kids,
        }
        if detail_view:
            data["usage"] = {
                "characters": [],
                "dictionaryEntries": [],
                "songs": [],
                "stories": [],
                "total": 0,
            }
        return data

    def get_file_data(self, file):
        return {
            "path": f"http://testserver{file.content.url}",
            "mimetype": file.mimetype,
            "size": file.size,
        }

    def get_visual_file_data(self, file):
        if file:
            return {
                **self.get_file_data(file),
                "height": file.height,
                "width": file.width,
            }
        else:
            return None

    def get_media_thumbnail_data(self, instance):
        return {
            "thumbnail": self.get_visual_file_data(instance.thumbnail),
            "small": self.get_visual_file_data(instance.small),
            "medium": self.get_visual_file_data(instance.medium),
        }

    def get_visual_media_data(self, instance, view_name, detail_view):
        data = self.get_basic_media_data(
            instance, view_name=view_name, detail_view=detail_view
        )
        thumbnail_data = self.get_media_thumbnail_data(instance)

        data = {
            **data,
            **thumbnail_data,
            "original": self.get_visual_file_data(instance.original),
        }

        if detail_view:
            data["usage"]["customPages"] = []

        return data

    def get_expected_image_data(self, instance, detail_view=False):
        data = self.get_visual_media_data(
            instance, view_name="api:image-detail", detail_view=detail_view
        )

        if detail_view:
            data["usage"]["gallery"] = []
            data["usage"]["siteBanner"] = {}
            data["usage"]["siteLogo"] = {}

        return data

    def get_expected_video_data(self, instance, detail_view=False):
        return self.get_visual_media_data(
            instance, view_name="api:video-detail", detail_view=detail_view
        )

    def get_expected_audio_data(self, instance, speaker, detail_view=False):
        data = self.get_basic_media_data(
            instance, view_name="api:audio-detail", detail_view=detail_view
        )
        data["original"] = self.get_file_data(instance.original)

        if speaker:
            speaker_url = reverse(
                "api:person-detail",
                current_app=self.APP_NAME,
                args=[speaker.site.slug, speaker.id],
            )

            data["speakers"] = [
                {
                    "url": f"http://testserver{speaker_url}",
                    "id": str(speaker.id),
                    "name": speaker.name,
                    "bio": speaker.bio,
                }
            ]
        else:
            data["speakers"] = []

        return data


class RelatedMediaTestMixin(MediaTestMixin):
    """
    For APIs that use the RelatedMediaSerializerMixin.
    """

    model = None

    def create_instance_with_media(
        self,
        site,
        visibility,
        related_images=None,
        related_audio=None,
        related_videos=None,
        related_video_links=None,
    ):
        raise NotImplementedError

    def assert_patch_instance_original_fields_related_media(
        self, original_instance, updated_instance
    ):
        assert updated_instance.related_audio == original_instance.related_audio
        assert updated_instance.related_images == original_instance.related_images
        assert updated_instance.related_videos == original_instance.related_videos

    def assert_update_patch_response_related_media(
        self, original_instance, actual_response
    ):
        assert actual_response["relatedAudio"][0]["id"] == str(
            original_instance.related_audio.first().id
        )
        assert actual_response["relatedImages"][0]["id"] == str(
            original_instance.related_images.first().id
        )
        assert actual_response["relatedVideos"][0]["id"] == str(
            original_instance.related_videos.first().id
        )

    def assert_update_response_related_media(self, expected_data, actual_response):
        assert len(actual_response["relatedAudio"]) == len(
            expected_data["relatedAudio"]
        )
        for i, a in enumerate(expected_data["relatedAudio"]):
            assert actual_response["relatedAudio"][i]["id"] == a

        assert len(actual_response["relatedVideos"]) == len(
            expected_data["relatedVideos"]
        )
        for i, v in enumerate(expected_data["relatedVideos"]):
            assert actual_response["relatedVideos"][i]["id"] == v

        assert len(actual_response["relatedImages"]) == len(
            expected_data["relatedImages"]
        )
        for i, img in enumerate(expected_data["relatedImages"]):
            assert actual_response["relatedImages"][i]["id"] == img

        assert (
            actual_response["relatedVideoLinks"] == expected_data["relatedVideoLinks"]
        )

    @pytest.mark.django_db
    def test_detail_related_audio_with_speaker(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        speaker = factories.PersonFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        factories.AudioSpeakerFactory.create(speaker=speaker, audio=audio)

        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_audio=(audio,)
        )

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["relatedAudio"]) == 1
        assert response_data["relatedAudio"][0] == self.get_expected_audio_data(
            audio, speaker, detail_view=False
        )

    @pytest.mark.django_db
    def test_detail_related_images(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        image = factories.ImageFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_images=(image,)
        )
        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["relatedImages"]) == 1

        expected = self.get_expected_image_data(image, detail_view=False)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in response_data["relatedImages"][0]:
                response_data["relatedImages"][0].pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert response_data["relatedImages"][0] == expected

    @pytest.mark.django_db
    def test_detail_related_videos(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        video = factories.VideoFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_videos=(video,)
        )
        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["relatedVideos"]) == 1

        expected = self.get_expected_video_data(video, detail_view=False)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in response_data["relatedVideos"][0]:
                response_data["relatedVideos"][0].pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert response_data["relatedVideos"][0] == expected

    @pytest.mark.parametrize(
        "related_video_links, expected_response_codes",
        [
            ([YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK], [200, 201]),
            (
                [
                    "https://www.youtube.com/watch?v=abc1",
                    "https://www.youtube.com/watch?v=abc2",
                ],
                [200, 201],
            ),
            (
                [
                    YOUTUBE_VIDEO_LINK,
                    VIMEO_VIDEO_LINK,
                    VIMEO_VIDEO_LINK,
                ],
                [400],
            ),
            (
                [
                    "https://www.youtube.com/watch?v=abc",
                    "https://www.youtube.com/watch?v=abc",
                ],
                [400],
            ),
        ],
    )
    @pytest.mark.django_db
    def test_update_duplicate_related_video_links(
        self, related_video_links, expected_response_codes
    ):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )

        instance = self.create_instance_with_media(
            site=site,
            visibility=Visibility.TEAM,
            related_video_links=[],
        )

        req_body = {"related_video_links": related_video_links}

        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        assert response.status_code in expected_response_codes

    @pytest.mark.django_db
    def test_update_remove_related_video_links(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )

        instance = self.create_instance_with_media(
            site=site,
            visibility=Visibility.TEAM,
            related_video_links=[YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK],
        )

        req_body = {"related_video_links": []}

        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        response_data = json.loads(response.content)

        assert response.status_code in [200, 201]
        assert response_data["relatedVideoLinks"] == []


class BaseMediaApiTest(
    MediaTestMixin,
    FormDataMixin,
    base_api_test.BaseUncontrolledSiteContentApiTest,
):
    """
    Tests for the list, detail, create, and delete APIs for media endpoints.
    """

    sample_filename = "sample-image.jpg"
    sample_filetype = "image/jpeg"
    model = None

    # Overriding methods to add in the detail_view parameter as that affects the response in case of media APIs
    def get_expected_detail_response(self, instance, site):
        return self.get_expected_response(instance, site, detail_view=True)

    def get_expected_list_response_item(self, instance, site):
        return self.get_expected_response(instance, site, detail_view=False)

    def get_valid_data(self, site=None):
        """Returns a valid data object suitable for create/update requests"""
        return {
            "title": "A title for the media",
            "description": "Description of the media",
            "acknowledgement": "An acknowledgement of the media",
            "excludeFromGames": True,
            "excludeFromKids": True,
            "original": self.get_sample_file(
                self.sample_filename, self.sample_filetype
            ),
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "A title for the media",
            "original": self.get_sample_file(
                self.sample_filename, self.sample_filetype
            ),
        }

    def add_expected_defaults(self, data):
        return {
            **data,
            "description": "",
            "acknowledgement": "",
            "excludeFromGames": False,
            "excludeFromKids": False,
        }

    def get_invalid_patch_data(self):
        """Add some actually invalid data-- empty data doesn't work for multipart encoder"""
        return {
            "excludeFromKids": "not a boolean value",
        }

    def get_valid_patch_data(self, site):
        return {
            "title": "A new title",
        }

    def get_valid_patch_file_data(self, site):
        return {
            "original": self.get_sample_file(
                self.sample_filename,
                self.sample_filetype,
                f"patch-{self.sample_filename}",
            ),
        }

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        assert instance.title == data["title"]
        assert instance.description == data["description"]

        # Split the filename and extension from the file paths and check for each to avoid async tests appending
        # characters to the end of the filename when file path already exists.
        data_filename = data["original"].name.split(".")[0]
        data_file_extension = data["original"].name.split(".")[1]
        instance_filename = instance.original.content.name.split(".")[0]
        instance_file_extension = instance.original.content.name.split(".")[1]
        assert data_filename in instance_filename
        assert data_file_extension in instance_file_extension

        assert instance.acknowledgement == data["acknowledgement"]
        assert instance.exclude_from_games == data["excludeFromGames"]
        assert instance.exclude_from_kids == data["excludeFromKids"]

    def add_related_objects(self, instance):
        # related files are added as part of minimal instance; nothing extra to add here
        pass

    def assert_related_objects_deleted(self, instance):
        """Default test is for visual media with thumbnails"""
        self.assert_instance_deleted(instance.original)
        self.assert_instance_deleted(instance.medium)
        self.assert_instance_deleted(instance.small)
        self.assert_instance_deleted(instance.thumbnail)

    def assert_secondary_fields(self, expected_data, updated_instance):
        assert updated_instance.description == expected_data["description"]
        assert updated_instance.acknowledgement == expected_data["acknowledgement"]
        assert updated_instance.exclude_from_kids == expected_data["excludeFromKids"]
        assert updated_instance.exclude_from_games == expected_data["excludeFromGames"]

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        assert updated_instance.title == data["title"]

    def assert_response(self, original_instance, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["description"] == expected_data["description"]
        assert actual_response["acknowledgement"] == expected_data["acknowledgement"]
        assert actual_response["excludeFromKids"] == expected_data["excludeFromKids"]
        assert actual_response["excludeFromGames"] == expected_data["excludeFromGames"]

        # The original file should not be updated, as it's a read-only field
        expected_file_path = (
            original_instance.original.content.url
            if hasattr(original_instance.original, "content")
            else original_instance.original.name
        )
        expected_filename = expected_file_path.split(".")[0]
        expected_file_extension = expected_file_path.split(".")[1]
        actual_filename = actual_response["original"]["path"].split(".")[0]
        actual_file_extension = actual_response["original"]["path"].split(".")[1]
        assert expected_filename in actual_filename
        assert expected_file_extension in actual_file_extension

    def assert_update_patch_file_response(
        self, original_instance, data, actual_response
    ):
        expected_data = {
            "id": str(original_instance.id),
            "title": original_instance.title,
            "description": original_instance.description,
            "acknowledgement": original_instance.acknowledgement,
            "excludeFromKids": original_instance.exclude_from_kids,
            "excludeFromGames": original_instance.exclude_from_games,
            "original": data["original"],
        }

        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data=expected_data,
        )

    def assert_update_response_media(
        self, original_instance, expected_data, actual_response
    ):
        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data={**expected_data},
        )

    @pytest.mark.django_db
    def test_create_400_invalid_filetype(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        data = self.get_valid_data(site)
        data["original"] = (self.get_sample_file("file.txt", self.sample_filetype),)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    def add_related_media_to_objects(self, visibility):
        # Add media file as related media to objects to verify that they show up correctly
        # in usage field when a media item is requested via detail view
        raise NotImplementedError

    @pytest.mark.django_db
    def test_usages_field_base(self):
        expected_data = self.add_related_media_to_objects(visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=expected_data["media_instance"].id,
                site_slug=expected_data["site"].slug,
            )
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        # usage in characters
        character_usage = response_data["usage"]["characters"]
        assert len(character_usage) == 1
        assert character_usage[0]["id"] == str(expected_data["character"].id)

        # usage in dictionary entries
        dict_entry_usage = response_data["usage"]["dictionaryEntries"]
        assert len(dict_entry_usage) == 1
        assert dict_entry_usage[0]["id"] == str(expected_data["dict_entry"].id)

        # usage in songs
        song_usage = response_data["usage"]["songs"]
        assert len(song_usage) == 1
        assert song_usage[0]["id"] == str(expected_data["song"].id)

        # usage in stories
        # Story pages point to the story, so the response here should only contain id's of both stories exactly once
        story_usage = response_data["usage"]["stories"]
        expected_stories_ids = [
            str(expected_data["stories"][0].id),
            str(expected_data["stories"][1].id),
        ]

        assert len(story_usage) == len(expected_data["stories"])
        assert story_usage[0]["id"] in expected_stories_ids
        assert story_usage[1]["id"] in expected_stories_ids

        assert response_data["usage"]["total"] == expected_data["total"]

    @pytest.mark.django_db
    def test_usages_field_permissions(self):
        expected_data = self.add_related_media_to_objects(visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_detail_endpoint(
                key=expected_data["media_instance"].id,
                site_slug=expected_data["site"].slug,
            )
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        # Characters visibility depends on the site's visibility, PUBLIC in this case
        assert len(response_data["usage"]["characters"]) == 1

        # controlled content should be available
        assert len(response_data["usage"]["dictionaryEntries"]) == 0
        assert len(response_data["usage"]["songs"]) == 0
        assert len(response_data["usage"]["stories"]) == 0


class BaseVisualMediaAPITest(BaseMediaApiTest):
    @pytest.fixture()
    def disable_celery(self, settings):
        # Sets the celery tasks to run synchronously for testing
        settings.CELERY_TASK_ALWAYS_EAGER = True

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
            },
            updated_instance=updated_instance,
        )

    def assert_update_patch_response(self, original_instance, data, actual_response):
        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data={
                "id": str(original_instance.id),
                "title": data["title"],
                "description": original_instance.description,
                "acknowledgement": original_instance.acknowledgement,
                "excludeFromKids": original_instance.exclude_from_kids,
                "excludeFromGames": original_instance.exclude_from_games,
                "original": original_instance.original,
            },
        )

    def assert_updated_instance(self, expected_data, actual_instance):
        self.assert_secondary_fields(expected_data, actual_instance)
        assert actual_instance.title == expected_data["title"]

    def assert_update_response(self, expected_data, actual_response):
        self.assert_response(
            actual_response=actual_response,
            expected_data={**expected_data},
        )

    @pytest.mark.django_db
    def test_patch_file_is_ignored(self):
        # PUT/PATCH requests updating the original file should be ignored,
        # i.e. there will be no validation error but the file will also not be updated.
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

        # Verifying the file does not change
        assert instance.original.content.name in response_data["original"]["path"]


def assert_patch_speaker_original_fields(self, original_instance, updated_instance):
    self.assert_original_secondary_fields(original_instance, updated_instance)
    assert updated_instance.title == original_instance.title
    assert updated_instance.original.id == original_instance.original.id
