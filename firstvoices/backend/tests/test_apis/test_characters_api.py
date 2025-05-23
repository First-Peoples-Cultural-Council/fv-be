import json

import pytest

from backend.models import Character
from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_api_test import WriteApiTestMixin
from backend.tests.test_apis.base.base_media_test import (
    MOCK_EMBED_LINK,
    MOCK_THUMBNAIL_LINK,
    VIMEO_VIDEO_LINK,
    YOUTUBE_VIDEO_LINK,
    RelatedMediaTestMixin,
)
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
    SiteContentPatchApiTestMixin,
)
from backend.tests.test_apis.test_dictionary_api import (
    assert_dictionary_entry_summary_response,
)


class TestCharactersEndpoints(
    RelatedMediaTestMixin,
    WriteApiTestMixin,
    SiteContentPatchApiTestMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:character-list"
    API_DETAIL_VIEW = "api:character-detail"
    CHARACTER_NOTE = "Test note"

    model = Character
    model_factory = factories.CharacterFactory

    def create_minimal_instance(self, site, visibility=None):
        return factories.CharacterFactory.create(
            site=site, note="a note", approximate_form="approx"
        )

    def create_instance_with_media(
        self,
        site,
        visibility,
        related_audio=None,
        related_documents=None,
        related_images=None,
        related_videos=None,
        related_video_links=None,
    ):
        if related_video_links is None:
            related_video_links = []
        return factories.CharacterFactory.create(
            site=site,
            related_audio=related_audio,
            related_documents=related_documents,
            related_images=related_images,
            related_videos=related_videos,
            related_video_links=related_video_links,
        )

    def get_expected_response(self, instance, site):
        standard_fields = self.get_expected_entry_standard_fields(instance, site)
        return {
            **standard_fields,
            "sortOrder": instance.sort_order,
            "approximateForm": instance.approximate_form,
            "note": instance.note,
            "variants": [],
            "relatedDictionaryEntries": [],
            **self.RELATED_MEDIA_DEFAULTS,
        }

    def create_original_instance_for_patch(self, site):
        related_media = self.get_related_media_for_patch(site=site)
        character = factories.CharacterFactory.create(
            site=site,
            title="Title",
            sort_order=2,
            approximate_form="test",
            note="Note",
            **related_media,
        )
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=dictionary_entry
        )

        return character

    def get_valid_patch_data(self, site=None):
        return {"note": "Note Updated"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: Character
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.title == original_instance.title
        assert updated_instance.sort_order == original_instance.sort_order
        assert updated_instance.approximate_form == original_instance.approximate_form
        self.assert_patch_instance_original_fields_related_media(
            original_instance, updated_instance
        )

    def assert_patch_instance_updated_fields(self, data, updated_instance: Character):
        assert updated_instance.note == data["note"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        self.assert_update_patch_response_related_media(
            original_instance, actual_response
        )
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["title"] == original_instance.title
        assert actual_response["sortOrder"] == original_instance.sort_order
        assert actual_response["approximateForm"] == original_instance.approximate_form
        assert actual_response["note"] == data["note"]
        assert actual_response["relatedDictionaryEntries"][0]["id"] == str(
            original_instance.related_dictionary_entries.first().id
        )

    @pytest.mark.django_db
    def test_detail_variants(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        character0 = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            note=self.CHARACTER_NOTE,
        )

        character1 = factories.CharacterFactory.create(
            title="Ch1", site=site, sort_order=2, approximate_form="Ch1", note=""
        )

        variant = factories.CharacterVariantFactory.create(
            title="Ch0v0", base_character=character0
        )
        factories.CharacterVariantFactory.create(
            title="Ch0v1", base_character=character1
        )

        response = self.client.get(
            self.get_detail_endpoint(key=character0.id, site_slug=site.slug)
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["id"] == str(character0.id)
        assert len(response_data["variants"]) == 1
        assert response_data["variants"] == [
            {
                "title": variant.title,
            }
        ]

    @pytest.mark.django_db
    def test_detail_related_entries(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        character = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            note=self.CHARACTER_NOTE,
        )

        entry1 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=entry1
        )
        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=entry2
        )

        response = self.client.get(
            self.get_detail_endpoint(key=character.id, site_slug=site.slug)
        )

        request = response.wsgi_request

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["id"] == str(character.id)
        assert len(response_data["relatedDictionaryEntries"]) == 1
        for entry in response_data["relatedDictionaryEntries"]:
            assert_dictionary_entry_summary_response(entry, entry1, request)

    # /------------------------------------------------------------------\
    # |  The following tests can be converted into a generic set of tests in the RelatedMediaTestMixin          |
    # |  once the write endpoints are implemented for all models that have related media.                       |

    @pytest.mark.django_db
    def test_update_related_audio(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )
        speaker = factories.PersonFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        factories.AudioSpeakerFactory.create(speaker=speaker, audio=audio)

        instance = self.create_instance_with_media(
            site=site,
            visibility=Visibility.TEAM,
            related_audio=(audio,),
        )

        new_audio = factories.AudioFactory.create(site=site)
        factories.AudioSpeakerFactory.create(speaker=speaker, audio=new_audio)

        req_body = {"related_audio": [str(new_audio.id)]}

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["relatedAudio"]) == 1
        assert response_data["relatedAudio"][0] == self.get_expected_audio_data(
            new_audio, speaker
        )
        assert (
            Character.objects.get(id=instance.id).related_audio.all().first().id
            == new_audio.id
        )

    @pytest.mark.django_db
    def test_update_related_images(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )
        image = factories.ImageFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site,
            visibility=Visibility.TEAM,
            related_images=(image,),
        )

        new_image = factories.ImageFactory.create(site=site)

        req_body = {"related_images": [str(new_image.id)]}

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["relatedImages"]) == 1
        expected = self.get_expected_image_data(new_image)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in response_data["relatedImages"][0]:
                response_data["relatedImages"][0].pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert response_data["relatedImages"][0] == expected

        assert (
            Character.objects.get(id=instance.id).related_images.all().first().id
            == new_image.id
        )

    @pytest.mark.django_db
    def test_update_related_videos(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )
        video = factories.VideoFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site,
            visibility=Visibility.TEAM,
            related_videos=(video,),
        )

        new_video = factories.VideoFactory.create(site=site)

        req_body = {"related_videos": [str(new_video.id)]}

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["relatedVideos"]) == 1

        expected = self.get_expected_video_data(new_video)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in response_data["relatedVideos"][0]:
                response_data["relatedVideos"][0].pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert response_data["relatedVideos"][0] == expected

        assert (
            Character.objects.get(id=instance.id).related_videos.all().first().id
            == new_video.id
        )

    @pytest.mark.django_db
    def test_update_related_video_links(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )

        instance = self.create_instance_with_media(
            site=site,
            visibility=Visibility.TEAM,
            related_video_links=[YOUTUBE_VIDEO_LINK],
        )

        req_body = {"related_video_links": [VIMEO_VIDEO_LINK]}

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["relatedVideoLinks"]) == 1

        assert response_data["relatedVideoLinks"][0] == {
            "videoLink": VIMEO_VIDEO_LINK,
            "embedLink": MOCK_EMBED_LINK,
            "thumbnail": MOCK_THUMBNAIL_LINK,
        }

    # \------------------------------------------------------------------/

    @pytest.mark.django_db
    def test_update_character_fields(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )
        character = factories.CharacterFactory.create(site=site)
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)

        req_body = {
            "note": self.CHARACTER_NOTE,
            "related_dictionary_entries": [str(dictionary_entry.id)],
        }

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.get_detail_endpoint(key=character.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["note"] == req_body["note"]
        assert len(response_data["relatedDictionaryEntries"]) == 1
        assert response_data["relatedDictionaryEntries"][0]["id"] == str(
            dictionary_entry.id
        )

        assert Character.objects.get(id=character.id).note == req_body["note"]
        assert (
            Character.objects.get(id=character.id).related_dictionary_entries.first().id
            == dictionary_entry.id
        )

    @pytest.mark.django_db
    def test_update_character_same_site_validation(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )
        site2 = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        character = factories.CharacterFactory.create(site=site)
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site2)

        req_body = {
            "note": self.CHARACTER_NOTE,
            "related_dictionary_entries": [str(dictionary_entry.id)],
        }

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.get_detail_endpoint(key=character.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "invalid_data_key, invalid_data_value",
        [
            ("related_audio", [1234]),
            ("related_documents", [1234]),
            ("related_images", [1234]),
            ("related_videos", [1234]),
            (
                "related_video_links",
                ["https://www.soundcloud.com/", "https://invalid.com/"],
            ),
        ],
    )
    @pytest.mark.django_db
    def test_update_character_invalid_media(self, invalid_data_key, invalid_data_value):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )
        character = factories.CharacterFactory.create(site=site)
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)

        req_body = {
            "note": self.CHARACTER_NOTE,
            "related_dictionary_entries": [str(dictionary_entry.id)],
            invalid_data_key: invalid_data_value,
        }

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.get_detail_endpoint(key=character.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_update_character_invalid_related_entries(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )
        character = factories.CharacterFactory.create(site=site)

        req_body = {
            "note": self.CHARACTER_NOTE,
            "related_dictionary_entries": ["123"],
        }

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.get_detail_endpoint(key=character.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )

        assert response.status_code == 400
