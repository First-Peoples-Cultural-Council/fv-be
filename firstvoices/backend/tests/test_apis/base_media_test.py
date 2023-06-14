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


class RelatedMediaTestMixin:
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
    def test_detail_related_audio(self):
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

        app = "backend"
        assert response_data["relatedAudio"][0] == {
            "id": str(audio.id),
            "title": audio.title,
            "content": f"http://testserver{audio.original.content.url}",
            "speakers": [
                {
                    "url": "http://testserver"
                    + f"{reverse('api:person-detail',current_app=app,args=[speaker.site.slug, str(speaker.id)],)}",
                    "id": str(speaker.id),
                    "name": speaker.name,
                    "bio": speaker.bio,
                }
            ],
        }

    @pytest.mark.django_db
    def test_detail_related_images(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        image = ImageFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_images=(image,)
        )
        self.assert_related_media(instance, site, "relatedImages", image)

    @pytest.mark.django_db
    def test_detail_related_videos(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        video = VideoFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_videos=(video,)
        )
        self.assert_related_media(instance, site, "relatedVideos", video)

    def assert_related_media(self, instance, site, media_key, media_instance):
        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data[media_key]) == 1
        assert response_data[media_key][0] == {
            "id": str(media_instance.id),
            "title": media_instance.title,
            "content": f"http://testserver{media_instance.original.content.url}",
        }
