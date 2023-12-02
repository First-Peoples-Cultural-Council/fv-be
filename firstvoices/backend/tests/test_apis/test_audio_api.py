import json

import pytest

from backend.models.constants import Visibility
from backend.models.media import Audio
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
    model = Audio

    def create_minimal_instance(self, site, visibility):
        return factories.AudioFactory.create(site=site)

    def create_original_instance_for_patch(self, site):
        speaker = factories.PersonFactory(site=site)
        audio = factories.AudioFactory.create(
            site=site,
            title="Original title",
            description="Original description",
            acknowledgement="Original ack",
            exclude_from_kids=True,
            exclude_from_games=True,
            is_shared=True,
        )
        audio.speakers.add(speaker)
        audio.save()
        return audio

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

    def assert_created_response(self, expected_data, actual_response):
        instance = Audio.objects.get(pk=actual_response["id"])
        assert actual_response == self.get_expected_audio_data(instance, None)

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

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        # everything but title
        assert updated_instance.description == original_instance.description
        assert updated_instance.acknowledgement == original_instance.acknowledgement
        assert updated_instance.exclude_from_kids == original_instance.exclude_from_kids
        assert (
            updated_instance.exclude_from_games == original_instance.exclude_from_games
        )
        assert updated_instance.is_shared == original_instance.is_shared
        assert updated_instance.original.id == original_instance.original.id
        assert updated_instance.speakers.count() == original_instance.speakers.count()
        assert (
            updated_instance.speakers.first().id
            == original_instance.speakers.first().id
        )

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
                "exclude_from_kids": original_instance.exclude_from_kids,
                "exclude_from_games": original_instance.exclude_from_games,
                "is_shared": original_instance.is_shared,
                "original": original_instance.original,
                "speakers": original_instance.speakers,
            },
        )

    def assert_response(self, expected_data, actual_response):
        assert actual_response["id"] == expected_data["id"]
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["description"] == expected_data["description"]
        assert actual_response["acknowledgement"] == expected_data["acknowledgement"]
        assert actual_response["excludeFromKids"] == expected_data["exclude_from_kids"]
        assert (
            actual_response["excludeFromGames"] == expected_data["exclude_from_games"]
        )
        assert actual_response["isShared"] == expected_data["is_shared"]
        assert (
            expected_data["original"].content.url in actual_response["original"]["path"]
        )
        assert len(actual_response["speakers"]) == expected_data["speakers"].count()
        assert actual_response["speakers"][0]["id"] == str(
            expected_data["speakers"].first().id
        )

    # todo: test patching original and speakers
    # @pytest.mark.django_db
    # def test_patch_file_success_200(self):
    #     site = self.create_site_with_app_admin(Visibility.PUBLIC)
    #     instance = self.create_original_instance_for_patch(site=site)
    #     data = self.get_valid_patch_file_data(site)
    #
    #     response = self.client.patch(
    #         self.get_detail_endpoint(
    #             key=self.get_lookup_key(instance), site_slug=site.slug
    #         ),
    #         data=self.format_upload_data(data),
    #         content_type=self.content_type,
    #     )
    #
    #     assert response.status_code == 200
    #     response_data = json.loads(response.content)
    #     assert response_data["id"] == str(instance.id)
    #
    #     self.assert_patch_file_original_fields(
    #         instance, self.get_updated_patch_instance(instance)
    #     )
    #     self.assert_patch_file_updated_fields(
    #         data, self.get_updated_patch_instance(instance)
    #     )
    #     self.assert_update_patch_file_response(instance, data, response_data)
