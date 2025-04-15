import json

import pytest

from backend.models.constants import Visibility
from backend.models.media import Audio
from backend.tests import factories
from backend.tests.test_apis.base.base_media_test import BaseMediaApiTest


class TestAudioEndpoint(BaseMediaApiTest):
    """
    End-to-end tests that the audio endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:audio-list"
    API_DETAIL_VIEW = "api:audio-detail"
    sample_filename = "sample-audio.mp3"
    sample_filetype = "audio/mpeg"
    model = Audio
    model_factory = factories.AudioFactory
    related_key = "related_audio"
    content_type_json = "application/json"

    def create_original_instance_for_patch(self, site):
        speaker = factories.PersonFactory(site=site)
        audio = factories.AudioFactory.create(
            site=site,
            title="Original title",
            description="Original description",
            acknowledgement="Original ack",
            exclude_from_kids=True,
            exclude_from_games=True,
        )
        audio.speakers.add(speaker)
        audio.save()
        return audio

    def get_expected_response(self, instance, site, detail_view=False):
        return self.get_expected_audio_data(
            instance, speaker=None, detail_view=detail_view
        )

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
        assert response_data == self.get_expected_audio_data(instance, speaker, True)

    def assert_created_response(
        self, expected_data, actual_response, detail_view=False
    ):
        instance = Audio.objects.get(pk=actual_response["id"])
        assert actual_response == self.get_expected_audio_data(
            instance, None, detail_view
        )

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
        self.assert_original_secondary_fields(original_instance, updated_instance)
        assert updated_instance.original.id == original_instance.original.id
        assert updated_instance.speakers.count() == original_instance.speakers.count()

    def assert_response(self, original_instance, expected_data, actual_response):
        super().assert_response(original_instance, expected_data, actual_response)
        expected_speaker_ids = []

        if "speakers" in expected_data:
            expected_speaker_ids = (
                [str(x[0]) for x in expected_data["speakers"].all().values_list("id")]
                if hasattr(expected_data["speakers"], "all")
                else expected_data["speakers"]
            )

        assert len(expected_speaker_ids) == len(actual_response["speakers"])
        for i, s in enumerate(expected_speaker_ids):
            assert actual_response["speakers"][i]["id"] == s

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
                "speakers": original_instance.speakers,
            },
        )

    def assert_updated_instance(self, expected_data, actual_instance):
        self.assert_secondary_fields(expected_data, actual_instance)
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.speakers.count() == 0

    def assert_update_response_audio(
        self, original_instance, expected_data, actual_response
    ):
        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data={**expected_data},
        )

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
            "speakers": original_instance.speakers,
        }
        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data=expected_data,
        )

    def assert_patch_file_original_fields(self, original_instance, updated_instance):
        self.assert_original_secondary_fields(original_instance, updated_instance)
        assert updated_instance.title == original_instance.title
        assert updated_instance.speakers.count() == original_instance.speakers.count()

    def assert_patch_file_updated_fields(self, data, updated_instance):
        assert data["original"].name in updated_instance.original.content.path

    def get_valid_patch_speaker_data(self, site):
        person1 = factories.PersonFactory.create(site=site)
        person2 = factories.PersonFactory.create(site=site)

        return {"speakers": [str(person1.id), str(person2.id)]}

    def assert_patch_speaker_original_fields(self, original_instance, updated_instance):
        self.assert_original_secondary_fields(original_instance, updated_instance)
        assert updated_instance.title == original_instance.title
        assert updated_instance.original.id == original_instance.original.id

    def assert_patch_speaker_updated_fields(self, data, updated_instance: Audio):
        actual_speaker_ids = [
            str(x[0]) for x in updated_instance.speakers.all().values_list("id")
        ]
        for speaker_id in data["speakers"]:
            assert speaker_id in actual_speaker_ids

    def assert_update_patch_speaker_response(
        self, original_instance, data, actual_response
    ):
        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data={
                "id": str(original_instance.id),
                "title": original_instance.title,
                "description": original_instance.description,
                "acknowledgement": original_instance.acknowledgement,
                "excludeFromKids": original_instance.exclude_from_kids,
                "excludeFromGames": original_instance.exclude_from_games,
                "original": original_instance.original,
                "speakers": data["speakers"],
            },
        )

    # Only testing for updating the speakers list.
    # Setting it to an empty list is tested below using content-type application/json
    @pytest.mark.django_db
    def test_patch_speakers_success_200(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_original_instance_for_patch(site=site)
        data = self.get_valid_patch_speaker_data(site)

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

        self.assert_patch_speaker_original_fields(
            instance, self.get_updated_patch_instance(instance)
        )
        self.assert_patch_speaker_updated_fields(
            data, self.get_updated_patch_instance(instance)
        )
        self.assert_update_patch_speaker_response(instance, data, response_data)

    # Setting speakers list to an empty array
    @pytest.mark.django_db
    def test_patch_speakers_success_200_empty(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_original_instance_for_patch(site=site)
        data = {"speakers": []}

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=json.dumps(data),
            content_type=self.content_type_json,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(instance.id)

        self.assert_patch_speaker_original_fields(
            instance, self.get_updated_patch_instance(instance)
        )
        self.assert_patch_speaker_updated_fields(
            data, self.get_updated_patch_instance(instance)
        )
        self.assert_update_patch_speaker_response(instance, data, response_data)

    # Setting speakers list to an empty array
    @pytest.mark.django_db
    def test_update_speakers_success_200_empty(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        # Setting speakers to an empty list
        # removing file, since that is not json serializable
        del data["original"]
        data["speakers"] = []

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=json.dumps(data),
            content_type=self.content_type_json,
        )
        response_data = json.loads(response.content)
        assert response_data["speakers"] == []
