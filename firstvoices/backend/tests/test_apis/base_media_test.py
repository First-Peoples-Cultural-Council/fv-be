import json
import os
import sys

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test.client import encode_multipart
from rest_framework.reverse import reverse

from backend.models.constants import Visibility
from backend.tests import factories
from backend.tests.test_apis import base_api_test


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

    def get_sample_file(self, filename, mimetype):
        path = (
            os.path.dirname(os.path.realpath(__file__))
            + f"/../factories/resources/{filename}"
        )
        image_file = open(path, "rb")
        return InMemoryUploadedFile(
            image_file,
            "FileField",
            filename,
            mimetype,
            sys.getsizeof(image_file),
            None,
        )

    def get_basic_media_data(self, instance, view_name):
        url = reverse(
            view_name, current_app=self.APP_NAME, args=[instance.site.slug, instance.id]
        )

        return {
            "id": str(instance.id),
            "url": f"http://testserver{url}",
            "title": instance.title,
            "description": instance.description,
            "acknowledgement": instance.acknowledgement,
            "excludeFromGames": instance.exclude_from_games,
            "excludeFromKids": instance.exclude_from_kids,
            "isShared": instance.is_shared,
        }

    def get_file_data(self, file):
        return {
            "path": f"http://testserver{file.content.url}",
            "mimetype": file.mimetype,
            "size": file.size,
        }

    def get_visual_file_data(self, file):
        file_data = self.get_file_data(file)
        file_data["height"] = file.height
        file_data["width"] = file.width
        return file_data

    def get_media_thumbnail_data(self, instance):
        o = {}
        if instance.thumbnail is not None:
            o["thumbnail"] = self.get_visual_file_data(instance.thumbnail)

        if instance.small is not None:
            o["small"] = self.get_visual_file_data(instance.small)

        if instance.medium is not None:
            o["medium"] = self.get_visual_file_data(instance.medium)

        return o

    def get_visual_media_data(self, instance, view_name):
        data = self.get_basic_media_data(instance, view_name=view_name)
        thumbnail_data = self.get_media_thumbnail_data(instance)
        return (
            data
            | thumbnail_data
            | {
                "original": self.get_visual_file_data(instance.original),
            }
        )

    def get_expected_image_data(self, instance):
        return self.get_visual_media_data(instance, view_name="api:image-detail")

    def get_expected_video_data(self, instance):
        return self.get_visual_media_data(instance, view_name="api:video-detail")

    def get_expected_audio_data(self, instance, speaker):
        data = self.get_basic_media_data(instance, view_name="api:audio-detail")
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
            audio, speaker
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

        expected = self.get_expected_image_data(image)
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

        expected = self.get_expected_video_data(video)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in response_data["relatedVideos"][0]:
                response_data["relatedVideos"][0].pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert response_data["relatedVideos"][0] == expected


class BaseMediaApiTest(
    MediaTestMixin,
    FormDataMixin,
    base_api_test.WriteApiTestMixin,
    base_api_test.SiteContentCreateApiTestMixin,
    base_api_test.SiteContentDestroyApiTestMixin,
    base_api_test.BaseReadOnlyUncontrolledSiteContentApiTest,
):
    """
    Tests for the list, detail, create, and delete APIs for media endpoints.
    """

    sample_filename = "sample-image.jpg"
    sample_filetype = "image/jpeg"
    model = None

    def get_valid_data(self, site=None):
        """Returns a valid data object suitable for create/update requests"""
        return {
            "title": "A title for the media",
            "description": "Description of the media",
            "acknowledgement": "An acknowledgement of the media",
            "isShared": True,
            "excludeFromGames": True,
            "excludeFromKids": True,
            "original": self.get_sample_file(
                self.sample_filename, self.sample_filetype
            ),
        }

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        assert instance.title == data["title"]
        assert instance.description == data["description"]
        assert data["original"].name in instance.original.content.name
        assert instance.acknowledgement == data["acknowledgement"]
        assert instance.is_shared == data["isShared"]
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
