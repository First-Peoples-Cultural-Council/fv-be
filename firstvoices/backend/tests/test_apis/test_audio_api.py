import json

import pytest

from backend.models.constants import Visibility
from backend.tests import factories

from .base_api_test import BaseReadOnlyUncontrolledSiteContentApiTest
from .base_media_test import MediaTestMixin


class TestAudioEndpoint(MediaTestMixin, BaseReadOnlyUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the audio endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:audio-list"
    API_DETAIL_VIEW = "api:audio-detail"

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
