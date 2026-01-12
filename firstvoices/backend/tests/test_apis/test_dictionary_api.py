import json

import pytest

from backend.models.constants import (
    MAX_ACKNOWLEDGEMENTS_PER_ENTRY,
    MAX_AUDIO_PER_ENTRY,
    MAX_CATEGORIES_PER_ENTRY,
    MAX_DOCUMENTS_PER_ENTRY,
    MAX_IMAGES_PER_ENTRY,
    MAX_NOTES_PER_ENTRY,
    MAX_PRONUNCIATIONS_PER_ENTRY,
    MAX_RELATED_ENTRIES_PER_ENTRY,
    MAX_SPELLINGS_PER_ENTRY,
    MAX_TRANSLATIONS_PER_ENTRY,
    MAX_VIDEOS_PER_ENTRY,
    Role,
    Visibility,
)
from backend.models.dictionary import (
    DictionaryEntry,
    ExternalDictionaryEntrySystem,
    TypeOfDictionaryEntry,
)
from backend.tests import factories
from backend.tests.test_apis.base.base_media_test import (
    VIMEO_VIDEO_LINK,
    YOUTUBE_VIDEO_LINK,
    RelatedMediaTestMixin,
)
from backend.tests.utils import (
    format_dictionary_entry_related_field,
    is_valid_uuid,
    to_camel_case,
)

from ...models import ImmersionLabel
from ...serializers.category_serializers import CategoryDetailSerializer
from ...serializers.dictionary_serializers import DictionaryEntrySummarySerializer
from ...serializers.media_serializers import (
    AudioSerializer,
    DocumentSerializer,
    ImageSerializer,
    RelatedVideoLinksSerializer,
    VideoSerializer,
)
from ...serializers.parts_of_speech_serializers import PartsOfSpeechSerializer
from .base.base_controlled_site_api import BaseControlledSiteContentApiTest


class TestDictionaryEndpoint(
    RelatedMediaTestMixin,
    BaseControlledSiteContentApiTest,
):
    """
    End-to-end tests that the dictionary endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:dictionaryentry-list"
    API_DETAIL_VIEW = "api:dictionaryentry-detail"

    NOTE_TEXT = "This is a note."
    TRANSLATION_TEXT = "This is a translation."

    model = DictionaryEntry
    model_factory = factories.DictionaryEntryFactory

    def create_minimal_instance(self, site, visibility):
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=visibility
        )
        return entry

    def get_valid_data(self, site=None):
        related_media = self.get_valid_related_media_data(site=site)
        pos = factories.PartOfSpeechFactory.create()

        return {
            "title": "Word",
            "type": "word",
            "visibility": "public",
            "customOrder": "⚑W⚑o⚑r⚑d",
            "categories": [],
            "excludeFromGames": True,
            "excludeFromKids": True,
            "acknowledgements": [{"text": "acknowledgements 1"}],
            "alternateSpellings": [{"text": "alternateSpellings 1"}],
            "notes": [{"text": "notes 1"}],
            "translations": [{"text": "translations 1"}],
            "partOfSpeech": str(pos.id),
            "pronunciations": [{"text": "pronunciations 1"}],
            "site": str(site.id),
            "relatedDictionaryEntries": [],
            "externalSystem": None,
            "externalSystemEntryId": "",
            **related_media,
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "Word",
            "type": "word",
            "visibility": "public",
            "site": str(site.id),
            "acknowledgements": [],
            "alternateSpellings": [],
            "notes": [],
            "translations": [],
            "pronunciations": [],
        }

    def add_expected_defaults(self, data):
        return {
            **data,
            "customOrder": "⚑W⚑o⚑r⚑d",
            "categories": [],
            "excludeFromGames": False,
            "excludeFromKids": False,
            "acknowledgements": [],
            "alternateSpellings": [],
            "notes": [],
            "translations": [],
            "partOfSpeech": None,
            "pronunciations": [],
            "relatedDictionaryEntries": [],
            **self.RELATED_MEDIA_DEFAULTS,
        }

    def add_related_objects(self, instance):
        # No related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # No related object to test deletion for
        pass

    def assert_updated_instance(self, expected_data, actual_instance: DictionaryEntry):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.type == expected_data["type"]
        assert list(actual_instance.categories.all()) == expected_data["categories"]
        assert actual_instance.exclude_from_games == expected_data["excludeFromGames"]
        assert actual_instance.exclude_from_kids == expected_data["excludeFromKids"]

        for index, acknowledgement in enumerate(actual_instance.acknowledgements):
            assert expected_data["acknowledgements"][index]["text"] == acknowledgement

        for index, note in enumerate(actual_instance.notes):
            assert expected_data["notes"][index]["text"] == note

        for index, translation in enumerate(actual_instance.translations):
            assert expected_data["translations"][index]["text"] == translation

        for index, alternate_spelling in enumerate(actual_instance.alternate_spellings):
            assert (
                expected_data["alternateSpellings"][index]["text"] == alternate_spelling
            )

        for index, pronunciation in enumerate(actual_instance.pronunciations):
            assert expected_data["pronunciations"][index]["text"] == pronunciation

        self.assert_updated_instance_related_media(expected_data, actual_instance)

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["type"] == expected_data["type"]
        assert actual_response["visibility"] == expected_data["visibility"]
        assert actual_response["categories"] == expected_data["categories"]
        assert actual_response["excludeFromGames"] == expected_data["excludeFromGames"]
        assert actual_response["excludeFromKids"] == expected_data["excludeFromKids"]

        acknowledgements = actual_response["acknowledgements"]
        assert len(acknowledgements) == len(expected_data["acknowledgements"])

        alternate_spellings = actual_response["alternateSpellings"]
        assert len(alternate_spellings) == len(expected_data["alternateSpellings"])

        notes = actual_response["notes"]
        assert len(notes) == len(expected_data["notes"])

        translations = actual_response["translations"]
        assert len(translations) == len(expected_data["translations"])

        pronunciations = actual_response["pronunciations"]
        assert len(pronunciations) == len(expected_data["pronunciations"])

        self.assert_update_response_related_media(expected_data, actual_response)

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        return self.get_expected_response(instance, instance.site)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def get_expected_list_response_item(self, entry, site):
        return self.get_expected_response(entry, site)

    def get_expected_response(self, instance, site):
        controlled_standard_fields = self.get_expected_controlled_standard_fields(
            instance, site
        )
        return {
            **controlled_standard_fields,
            "type": "word",
            "customOrder": instance.custom_order,
            "categories": [],
            "excludeFromGames": False,
            "excludeFromKids": False,
            "acknowledgements": format_dictionary_entry_related_field(
                instance.acknowledgements
            ),
            "alternateSpellings": format_dictionary_entry_related_field(
                instance.alternate_spellings
            ),
            "notes": format_dictionary_entry_related_field(instance.notes),
            "translations": format_dictionary_entry_related_field(
                instance.translations
            ),
            "partOfSpeech": (
                {
                    "id": str(instance.part_of_speech.id),
                    "title": instance.part_of_speech.title,
                    "parent": None,
                }
                if instance.part_of_speech
                else None
            ),
            "pronunciations": format_dictionary_entry_related_field(
                instance.pronunciations
            ),
            "relatedDictionaryEntries": [],
            **self.RELATED_MEDIA_DEFAULTS,
            "isImmersionLabel": False,
            "externalSystem": None,
            "externalSystemEntryId": "",
        }

    def create_original_instance_for_patch(self, site):
        related_media = self.get_related_media_for_patch(site=site)
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=site,
            title="Title",
            type=TypeOfDictionaryEntry.WORD,
            legacy_batch_filename="Legacy batch filename",
            exclude_from_wotd=True,
            **related_media,
            translations=["translation_1", "translation_2"],
            notes=["note_1", "note_2"],
            pronunciations=["pronunciation_1", "pronunciation_2"],
            acknowledgements=["acknowledgement_1", "acknowledgement_2"],
            alternate_spellings=["alternate_spelling_1", "alternate_spelling_2"],
        )

        entry_two = factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryLinkFactory.create(
            from_dictionary_entry=dictionary_entry, to_dictionary_entry=entry_two
        )

        category = factories.CategoryFactory.create(site=site)
        factories.DictionaryEntryCategoryFactory.create(
            category=category, dictionary_entry=dictionary_entry
        )

        character = factories.CharacterFactory.create(site=site)
        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=dictionary_entry
        )

        return dictionary_entry

    def get_valid_patch_data(self, site=None):
        return {"title": "Title Updated"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: DictionaryEntry
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.type == original_instance.type
        assert (
            updated_instance.legacy_batch_filename
            == original_instance.legacy_batch_filename
        )
        assert updated_instance.exclude_from_wotd == original_instance.exclude_from_wotd
        assert (
            updated_instance.categories.first().id
            == original_instance.categories.first().id
        )
        assert (
            updated_instance.related_dictionary_entries.first().id
            == original_instance.related_dictionary_entries.first().id
        )
        assert (
            updated_instance.related_characters.first().id
            == original_instance.related_characters.first().id
        )
        assert (
            updated_instance.exclude_from_games == original_instance.exclude_from_games
        )
        assert updated_instance.exclude_from_kids == original_instance.exclude_from_kids
        self.assert_patch_instance_original_fields_related_media(
            original_instance, updated_instance
        )

        assert updated_instance.acknowledgements == original_instance.acknowledgements
        assert (
            updated_instance.alternate_spellings
            == original_instance.alternate_spellings
        )
        assert updated_instance.notes == original_instance.notes
        assert updated_instance.translations == original_instance.translations
        assert updated_instance.pronunciations == original_instance.pronunciations

    def assert_patch_instance_updated_fields(
        self, data, updated_instance: DictionaryEntry
    ):
        assert updated_instance.title == data["title"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["title"] == data["title"]
        assert actual_response["type"] == original_instance.type
        assert (
            actual_response["visibility"]
            == original_instance.get_visibility_display().lower()
        )
        assert actual_response["categories"][0]["id"] == str(
            original_instance.categories.first().id
        )
        assert actual_response["relatedDictionaryEntries"][0]["id"] == str(
            original_instance.related_dictionary_entries.first().id
        )
        self.assert_update_patch_response_related_media(
            original_instance, actual_response
        )

    def assert_dictionary_entry_detail(self, instance, response_data, request_data):
        controlled_standard_fields = self.get_expected_controlled_standard_fields(
            instance, instance.site
        )
        for key, value in controlled_standard_fields.items():
            assert response_data[key] == value
        assert_dictionary_entry_detail_response(response_data, instance, request_data)

    @pytest.mark.skip(
        reason="Dictionary entry API does not have eligible optional charfields."
    )
    def test_create_with_null_optional_charfields_success_201(self):
        # Dictionary entry API does not have eligible optional charfields.
        pass

    @pytest.mark.skip(
        reason="Dictionary entry API does not have eligible optional charfields."
    )
    def test_update_with_null_optional_charfields_success_200(self):
        # Dictionary entry API does not have eligible optional charfields.
        pass

    @pytest.mark.django_db
    def test_detail_minimal(self):
        # overwriting the base test to test text list field ids
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.perform_successful_get_request_response(instance, site, True)
        request_data = response.wsgi_request
        response_data = json.loads(response.content)

        self.assert_dictionary_entry_detail(instance, response_data, request_data)

    @pytest.mark.django_db
    def test_list_minimal(self):
        # overwriting the base test to test text list field ids
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.perform_successful_get_request_response(instance, site, False)
        request_data = response.wsgi_request
        response_data = json.loads(response.content)

        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1
        response_data = json.loads(response.content)["results"][0]

        self.assert_dictionary_entry_detail(instance, response_data, request_data)

    @pytest.mark.django_db
    def test_list_permissions(self):
        # overwriting the base test to test text list field ids
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        self.create_minimal_instance(site=site, visibility=Visibility.MEMBERS)
        self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert_dictionary_entry_summary_response(
            response_data["results"][0], instance, response.wsgi_request
        )

        assert "createdBy" not in response_data["results"][0]
        assert "lastModifiedBy" not in response_data["results"][0]
        assert "systemLastModifiedBy" not in response_data["results"][0]

    @pytest.mark.django_db
    def test_detail_categories(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        category1 = factories.CategoryFactory(site=site, title="test category A")
        factories.CategoryFactory(site=site, title="test category B")
        factories.CategoryFactory(site=site)

        factories.DictionaryEntryCategoryFactory(
            category=category1, dictionary_entry=entry
        )

        response = self.client.get(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["categories"] == [
            {
                "title": f"{category1.title}",
                "id": str(category1.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}/categories/{str(category1.id)}",
            },
        ]

    @pytest.mark.django_db
    def test_detail_related_entries(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry3 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.TEAM
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)

        factories.DictionaryEntryLinkFactory(
            from_dictionary_entry=entry, to_dictionary_entry=entry2
        )
        factories.DictionaryEntryLinkFactory(
            from_dictionary_entry=entry, to_dictionary_entry=entry3
        )

        response = self.client.get(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )
        request_data = response.wsgi_request

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert (
            len(response_data["relatedDictionaryEntries"]) >= 1
        ), "Did not include related entry"
        assert (
            not len(response_data["relatedDictionaryEntries"]) > 1
        ), "Did not block private related entry"
        for entry in response_data["relatedDictionaryEntries"]:
            assert_dictionary_entry_summary_response(entry, entry2, request_data)

    @pytest.mark.django_db
    def test_detail_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(
            visibility=Visibility.TEAM, site=site
        )

        response = self.client.get(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(entry.id)

    @pytest.mark.django_db
    def test_dictionary_entry_create_invalid_related_entries(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        data = {
            "title": "Hello",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "public",
            "exclude_from_games": False,
            "exclude_from_kids": False,
            "related_dictionary_entries": [1234],
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
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
            (
                "related_video_links",
                ["https://www.vimeo.com/abc"],
            ),
            (
                "related_video_links",
                ["https://www.youtube.com/abc"],
            ),
        ],
    )
    @pytest.mark.django_db
    def test_dictionary_entry_create_invalid_related_media(
        self, invalid_data_key, invalid_data_value
    ):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        data = {
            "title": "Hello",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "public",
            "exclude_from_games": False,
            "exclude_from_kids": False,
            invalid_data_key: invalid_data_value,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "related_video_links, expected_response_code",
        [
            ([YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK], 201),
            (
                [
                    "https://www.youtube.com/watch?v=abc1",
                    "https://www.youtube.com/watch?v=abc2",
                ],
                201,
            ),
            (
                [
                    YOUTUBE_VIDEO_LINK,
                    VIMEO_VIDEO_LINK,
                    VIMEO_VIDEO_LINK,
                ],
                400,
            ),
            (
                [
                    "https://www.youtube.com/watch?v=abc",
                    "https://www.youtube.com/watch?v=abc",
                ],
                400,
            ),
        ],
    )
    @pytest.mark.django_db
    def test_dictionary_entry_create_duplicate_related_video_links(
        self, related_video_links, expected_response_code
    ):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        data = {
            "title": "Test Word One",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "public",
            "exclude_from_games": False,
            "exclude_from_kids": False,
            "related_video_links": related_video_links,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == expected_response_code

    @pytest.mark.django_db
    def test_dictionary_entry_update_invalid_related_entries(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)

        data = {
            "title": "Goodbye",
            "type": TypeOfDictionaryEntry.PHRASE,
            "visibility": "team",
            "exclude_from_games": True,
            "exclude_from_kids": True,
            "related_dictionary_entries": ["1234"],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "invalid_data_key, invalid_data_value",
        [
            ("related_audio", ["1234"]),
            ("related_images", ["1234"]),
            ("related_videos", ["1234"]),
            (
                "related_video_links",
                ["https://www.soundcloud.com/", "https://invalid.com/"],
            ),
            (
                "related_video_links",
                ["https://www.vimeo.com/abc"],
            ),
            (
                "related_video_links",
                ["https://www.youtube.com/abc"],
            ),
        ],
    )
    @pytest.mark.django_db
    def test_dictionary_entry_update_invalid_related_media(
        self, invalid_data_key, invalid_data_value
    ):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)

        data = {
            "title": "Goodbye",
            "type": TypeOfDictionaryEntry.PHRASE,
            "visibility": "team",
            "exclude_from_games": True,
            "exclude_from_kids": True,
            invalid_data_key: invalid_data_value,
        }

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_dictionary_entry_category_same_site_validation(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        site2 = factories.SiteFactory()
        category = factories.CategoryFactory.create(site=site2)
        entry = factories.DictionaryEntryFactory.create(site=site)

        data = {
            "title": "Hello",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "public",
            "categories": [str(category.id)],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_dictionary_entry_delete_does_not_delete_related_entry(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)
        related_entry = factories.DictionaryEntryFactory.create(site=site)

        entry.related_dictionary_entries.add(related_entry)

        response = self.client.delete(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )

        assert response.status_code == 204
        assert DictionaryEntry.objects.filter(id=entry.id).exists() is False
        assert DictionaryEntry.objects.filter(id=related_entry.id).exists() is True

    @pytest.mark.django_db
    def test_dictionary_entry_immersion_label_flag(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)

        response = self.client.get(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["isImmersionLabel"] is False

        factories.ImmersionLabelFactory.create(dictionary_entry=entry)

        response = self.client.get(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["isImmersionLabel"] is True

    @pytest.mark.django_db
    def test_dictionary_entry_create_invalid_fields_input(self):
        # Test for if the input for fields such as translations, acknowledgements and such is invalid

        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        data = {
            "title": "Test Word One",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "public",
            "exclude_from_games": False,
            "exclude_from_kids": False,
            "translations": [{"value": "abc"}],
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )
        response_data = json.loads(response.content)

        assert response.status_code == 400
        assert response_data["translations"] == [
            "Expected the objects in the list to contain key 'text'."
        ]

    @pytest.mark.django_db
    def test_dictionary_entry_create_external_system_fields(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        ExternalDictionaryEntrySystem.objects.create(title="External One")

        data = {
            "title": "Hello",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "team",
            "exclude_from_games": False,
            "exclude_from_kids": False,
            "external_system": "External One",
            "external_system_entry_id": "abc-123",
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )
        assert response.status_code == 201

        response_data = json.loads(response.content)
        assert response_data["externalSystem"] == "External One"
        assert response_data["externalSystemEntryId"] == "abc-123"

        entry_in_db = DictionaryEntry.objects.get(id=response_data["id"])
        assert (
            entry_in_db.external_system
            and entry_in_db.external_system.title == "External One"
        )
        assert entry_in_db.external_system_entry_id == "abc-123"

    @pytest.mark.django_db
    def test_dictionary_entry_update_external_system_fields_put(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        sys_a = ExternalDictionaryEntrySystem.objects.create(title="ExtA")
        sys_b = ExternalDictionaryEntrySystem.objects.create(title="ExtB")

        entry = factories.DictionaryEntryFactory.create(
            site=site,
            title="Hello",
            type=TypeOfDictionaryEntry.WORD,
            visibility=Visibility.PUBLIC,
            exclude_from_games=False,
            exclude_from_kids=False,
            external_system=sys_a,
            external_system_entry_id="old-id",
        )

        data = {
            "title": "Hello",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "public",
            "exclude_from_games": False,
            "exclude_from_kids": False,
            "external_system": "ExtB",
            "external_system_entry_id": "new-id",
        }

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )
        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["externalSystem"] == "ExtB"
        assert response_data["externalSystemEntryId"] == "new-id"

        entry.refresh_from_db()
        assert entry.external_system_id == sys_b.id
        assert entry.external_system_entry_id == "new-id"

    @pytest.mark.django_db
    def test_dictionary_entry_patch_clear_external_system_fields(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        system = ExternalDictionaryEntrySystem.objects.create(title="ExtClear")
        entry = factories.DictionaryEntryFactory.create(
            site=site,
            title="Hello",
            type=TypeOfDictionaryEntry.WORD,
            visibility=Visibility.PUBLIC,
            external_system=system,
            external_system_entry_id="to-clear",
        )

        data = {
            "external_system": None,
            "external_system_entry_id": "",
        }

        response = self.client.patch(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )
        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["externalSystem"] is None
        assert response_data["externalSystemEntryId"] == ""

        entry.refresh_from_db()
        assert entry.external_system is None
        assert entry.external_system_entry_id == ""

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "text_list_field, maximum_items",
        [
            ("acknowledgements", 10),
            ("alternate_spellings", 3),
            ("notes", 10),
            ("pronunciations", 3),
            ("translations", 10),
        ],
    )
    def test_dictionary_entry_text_list_field_limits_create(
        self, text_list_field, maximum_items
    ):
        site, user = factories.get_site_with_app_admin(client=self.client)

        data = {
            "title": "Test Word",
            "type": str(TypeOfDictionaryEntry.WORD),
            "visibility": "public",
            text_list_field: [{"text": f"item {i}"} for i in range(1, 12)],
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            response_data[to_camel_case(text_list_field)][0]
            == f"Maximum number of {text_list_field} exceeded. - Found: 11, Maximum allowed: {maximum_items}."
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "text_list_field, maximum_items",
        [
            ("acknowledgements", 10),
            ("alternate_spellings", 3),
            ("notes", 10),
            ("pronunciations", 3),
            ("translations", 10),
        ],
    )
    def test_dictionary_entry_text_list_field_limits_update(
        self, text_list_field, maximum_items
    ):
        site, user = factories.get_site_with_app_admin(client=self.client)
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)

        data = {
            "title": entry.title,
            "type": str(entry.type),
            "visibility": "public",
            text_list_field: [{"text": f"item {i}"} for i in range(1, 12)],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            response_data[to_camel_case(text_list_field)][0]
            == f"Maximum number of {text_list_field} exceeded. - Found: 11, Maximum allowed: {maximum_items}."
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "text_list_field, maximum_items",
        [
            ("acknowledgements", MAX_ACKNOWLEDGEMENTS_PER_ENTRY),
            ("alternate_spellings", MAX_SPELLINGS_PER_ENTRY),
            ("notes", MAX_NOTES_PER_ENTRY),
            ("pronunciations", MAX_PRONUNCIATIONS_PER_ENTRY),
            ("translations", MAX_TRANSLATIONS_PER_ENTRY),
        ],
    )
    def test_dictionary_entry_text_list_field_limits_patch(
        self, text_list_field, maximum_items
    ):
        site, user = factories.get_site_with_app_admin(client=self.client)
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)

        data = {
            text_list_field: [{"text": f"item {i}"} for i in range(1, 12)],
        }

        response = self.client.patch(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            response_data[to_camel_case(text_list_field)][0]
            == f"Maximum number of {text_list_field} exceeded. - Found: 11, Maximum allowed: {maximum_items}."
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "related_model_field, related_model_factory, maximum_items",
        [
            ("categories", factories.CategoryFactory, MAX_CATEGORIES_PER_ENTRY),
            (
                "related_dictionary_entries",
                factories.DictionaryEntryFactory,
                MAX_RELATED_ENTRIES_PER_ENTRY,
            ),
            ("related_audio", factories.AudioFactory, MAX_AUDIO_PER_ENTRY),
            ("related_documents", factories.DocumentFactory, MAX_DOCUMENTS_PER_ENTRY),
            ("related_images", factories.ImageFactory, MAX_IMAGES_PER_ENTRY),
            ("related_videos", factories.VideoFactory, MAX_VIDEOS_PER_ENTRY),
        ],
    )
    def test_dictionary_entry_related_model_field_limits_create(
        self, related_model_field, related_model_factory, maximum_items
    ):
        site, user = factories.get_site_with_app_admin(client=self.client)
        self.client.force_authenticate(user=user)
        related_items = [
            str(related_model_factory.create(site=site).id)
            for _ in range(maximum_items + 1)
        ]

        data = {
            "title": "Test Word",
            "type": str(TypeOfDictionaryEntry.WORD),
            "visibility": "public",
            related_model_field: related_items,
        }
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            response_data[to_camel_case(related_model_field)][0]
            == f"Maximum number of {related_model_field} exceeded. - "
            f"Found: {maximum_items + 1}, Maximum allowed: {maximum_items}."
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "related_model_field, related_model_factory, maximum_items",
        [
            ("categories", factories.CategoryFactory, MAX_CATEGORIES_PER_ENTRY),
            (
                "related_dictionary_entries",
                factories.DictionaryEntryFactory,
                MAX_RELATED_ENTRIES_PER_ENTRY,
            ),
            ("related_audio", factories.AudioFactory, MAX_AUDIO_PER_ENTRY),
            ("related_documents", factories.DocumentFactory, MAX_DOCUMENTS_PER_ENTRY),
            ("related_images", factories.ImageFactory, MAX_IMAGES_PER_ENTRY),
            ("related_videos", factories.VideoFactory, MAX_VIDEOS_PER_ENTRY),
        ],
    )
    def test_dictionary_entry_related_model_field_limits_update(
        self, related_model_field, related_model_factory, maximum_items
    ):
        site, user = factories.get_site_with_app_admin(client=self.client)
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)
        related_items = [
            str(related_model_factory.create(site=site).id)
            for _ in range(maximum_items + 1)
        ]

        data = {
            "title": entry.title,
            "type": str(entry.type),
            "visibility": "public",
            related_model_field: related_items,
        }
        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            response_data[to_camel_case(related_model_field)][0]
            == f"Maximum number of {related_model_field} exceeded. "
            f"- Found: {maximum_items + 1}, Maximum allowed: {maximum_items}."
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "related_model_field, related_model_factory, maximum_items",
        [
            ("categories", factories.CategoryFactory, MAX_CATEGORIES_PER_ENTRY),
            (
                "related_dictionary_entries",
                factories.DictionaryEntryFactory,
                MAX_RELATED_ENTRIES_PER_ENTRY,
            ),
            ("related_audio", factories.AudioFactory, MAX_AUDIO_PER_ENTRY),
            ("related_documents", factories.DocumentFactory, MAX_DOCUMENTS_PER_ENTRY),
            ("related_images", factories.ImageFactory, MAX_IMAGES_PER_ENTRY),
            ("related_videos", factories.VideoFactory, MAX_VIDEOS_PER_ENTRY),
        ],
    )
    def test_dictionary_entry_related_model_field_limits_patch(
        self, related_model_field, related_model_factory, maximum_items
    ):
        site, user = factories.get_site_with_app_admin(client=self.client)
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)
        related_items = [
            str(related_model_factory.create(site=site).id)
            for _ in range(maximum_items + 1)
        ]

        data = {
            related_model_field: related_items,
        }
        response = self.client.patch(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            response_data[to_camel_case(related_model_field)][0]
            == f"Maximum number of {related_model_field} exceeded. - "
            f"Found: {maximum_items + 1}, Maximum allowed: {maximum_items}."
        )


def assert_dictionary_entry_summary_response(data, entry, request_data):
    # standalone utility function to assert dictionary entry summary response
    assert data["id"] == str(entry.id)
    assert data["title"] == entry.title
    assert data["type"] == entry.type
    assert (
        data["url"]
        == f"http://testserver/api/1.0/sites/{entry.site.slug}/dictionary/{str(entry.id)}"
    )
    for index, translation in enumerate(entry.translations):
        assert is_valid_uuid(data["translations"][index]["id"])
        assert data["translations"][index]["text"] == translation

    assert (
        data["relatedAudio"]
        == AudioSerializer(
            entry.related_audio, context={"request": request_data}, many=True
        ).data
    )
    assert (
        data["relatedDocuments"]
        == DocumentSerializer(
            entry.related_documents, context={"request": request_data}, many=True
        ).data
    )
    assert (
        data["relatedImages"]
        == ImageSerializer(
            entry.related_images, context={"request": request_data}, many=True
        ).data
    )
    assert (
        data["relatedVideos"]
        == VideoSerializer(
            entry.related_videos, context={"request": request_data}, many=True
        ).data
    )
    assert (
        data["relatedVideoLinks"]
        == RelatedVideoLinksSerializer(
            entry.related_video_links, context={"request": request_data}, many=True
        ).data
    )


def assert_dictionary_entry_detail_response(data, entry, request_data):
    # standalone utility function to assert dictionary entry detail response
    assert_dictionary_entry_summary_response(data, entry, request_data)
    assert data["customOrder"] == entry.custom_order
    assert (
        data["categories"]
        == CategoryDetailSerializer(
            entry.categories, context={"request": request_data}, many=True
        ).data
    )
    assert data["excludeFromGames"] == entry.exclude_from_games
    assert data["excludeFromKids"] == entry.exclude_from_kids

    for index, acknowledgement in enumerate(entry.acknowledgements):
        assert is_valid_uuid(data["acknowledgements"][index]["id"])
        assert data["acknowledgements"][index]["text"] == acknowledgement
    for index, alternate_spelling in enumerate(entry.alternate_spellings):
        assert is_valid_uuid(data["alternateSpellings"][index]["id"])
        assert data["alternateSpellings"][index]["text"] == alternate_spelling
    for index, note in enumerate(entry.notes):
        assert is_valid_uuid(data["notes"][index]["id"])
        assert data["notes"][index]["text"] == note

    assert (
        data["partOfSpeech"]
        == PartsOfSpeechSerializer(
            entry.part_of_speech, context={"request": request_data}
        ).data
    )

    for index, pronunciation in enumerate(entry.pronunciations):
        assert is_valid_uuid(data["pronunciations"][index]["id"])
        assert data["pronunciations"][index]["text"] == pronunciation

    assert (
        data["relatedDictionaryEntries"]
        == DictionaryEntrySummarySerializer(
            entry.related_dictionary_entries,
            context={"request": request_data},
            many=True,
        ).data
    )
    assert (
        data["isImmersionLabel"]
        == ImmersionLabel.objects.filter(dictionary_entry=entry).exists()
    )
