import json

import pytest

from backend.models.constants import Visibility
from backend.tests import factories

from .base_media_test import BaseMediaApiTest


class TestAudioEndpoint(BaseMediaApiTest):
    """
    End-to-end tests that the audio endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:audio-list"
    API_DETAIL_VIEW = "api:audio-detail"
    sample_filename = "sample-audio.mp3"
    sample_filetype = "audio/mpeg"

    def create_minimal_instance(self, site, visibility):
        return factories.AudioFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return self.get_expected_audio_data(instance, speaker=None)

    @pytest.mark.django_db
    def test_detail_with_speakers(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=None)
        speaker = factories.PersonFactory.create(site=site, bio="bio")
        factories.AudioSpeakerFactory.create(audio=instance, speaker=speaker)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == self.get_expected_audio_data(instance, speaker)

    def assert_related_objects_deleted(self, instance):
        self.assert_instance_deleted(instance.original)

    @pytest.mark.django_db
    def test_create_with_speakers(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        speaker1 = factories.PersonFactory.create(site=site)
        speaker2 = factories.PersonFactory.create(site=site)
        data = self.get_valid_data(site)
        data["speakers"] = [str(speaker1.id), str(speaker2.id)]

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201
