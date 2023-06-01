import json

import pytest
from rest_framework.reverse import reverse

from backend.models.constants import Visibility
from backend.tests.factories import (
    AudioFactory,
    AudioSpeakerFactory,
    ImageFactory,
    PersonFactory,
    VideoFactory,
)


class MediaTestMixin:
    """
    Utilities for asserting media responses.
    """

    def get_basic_media_data(self, instance, view_name):
        url = reverse(
            view_name, current_app=self.APP_NAME, args=[instance.site.slug, instance.id]
        )

        return {
            "id": str(instance.id),
            "title": instance.title,
            "content": f"http://testserver{instance.original.content.url}",
            "url": f"http://testserver{url}",
        }

    def get_expected_image_data(self, instance):
        return self.get_basic_media_data(instance, view_name="api:image-detail")

    def get_expected_video_data(self, instance):
        return self.get_basic_media_data(instance, view_name="api:video-detail")

    def get_expected_audio_data(self, instance, speaker):
        data = self.get_basic_media_data(instance, view_name="api:audio-detail")

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

    @pytest.mark.django_db
    def test_detail_related_audio_with_speaker(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        speaker = PersonFactory.create(site=site)
        audio = AudioFactory.create(site=site)
        AudioSpeakerFactory.create(speaker=speaker, audio=audio, site=site)

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
        image = ImageFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_images=(image,)
        )
        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["relatedImages"]) == 1
        assert response_data["relatedImages"][0] == self.get_expected_image_data(image)

    @pytest.mark.django_db
    def test_detail_related_videos(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        video = VideoFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_videos=(video,)
        )
        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["relatedVideos"]) == 1
        assert response_data["relatedVideos"][0] == self.get_expected_video_data(video)
