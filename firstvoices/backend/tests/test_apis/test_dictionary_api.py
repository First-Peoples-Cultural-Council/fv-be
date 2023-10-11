import copy
import json

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.models.dictionary import (
    Acknowledgement,
    AlternateSpelling,
    DictionaryEntry,
    Note,
    Pronunciation,
    Translation,
    TypeOfDictionaryEntry,
)
from backend.tests import factories

from .base_api_test import BaseControlledSiteContentApiTest
from .base_media_test import RelatedMediaTestMixin


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

    def create_minimal_instance(self, site, visibility):
        return factories.DictionaryEntryFactory.create(site=site, visibility=visibility)

    def get_valid_data(self, site=None):
        related_images = []
        related_videos = []
        related_audio = []

        for _unused in range(3):
            related_images.append(factories.ImageFactory.create(site=site))
            related_videos.append(factories.VideoFactory.create(site=site))
            related_audio.append(factories.AudioFactory.create(site=site))

        return {
            "title": "Word",
            "type": "word",
            "visibility": "public",
            "customOrder": "⚑W⚑o⚑r⚑d",
            "categories": [],
            "excludeFromGames": True,
            "excludeFromKids": True,
            "acknowledgements": [],
            "alternateSpellings": [],
            "notes": [],
            "translations": [],
            "partOfSpeech": None,
            "pronunciations": [],
            "site": str(site.id),
            "relatedDictionaryEntries": [],
            "relatedAudio": list(map(lambda x: str(x.id), related_audio)),
            "relatedImages": list(map(lambda x: str(x.id), related_images)),
            "relatedVideos": list(map(lambda x: str(x.id), related_videos)),
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "Word",
            "type": "word",
            "visibility": "public",
            "site": str(site.id),
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
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
        }


    def add_related_objects(self, instance):
        factories.AcknowledgementFactory.create(dictionary_entry=instance)
        factories.AlternateSpellingFactory.create(dictionary_entry=instance)
        factories.NoteFactory.create(dictionary_entry=instance)
        factories.TranslationFactory.create(dictionary_entry=instance)
        factories.PronunciationFactory.create(dictionary_entry=instance)

    def assert_related_objects_deleted(self, instance):
        for model in (
            Acknowledgement,
            AlternateSpelling,
            Note,
            Translation,
            Pronunciation,
        ):
            assert model.objects.filter(dictionary_entry=instance).count() == 0

    def assert_updated_instance(self, expected_data, actual_instance: DictionaryEntry):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.type == expected_data["type"]
        assert list(actual_instance.categories.all()) == expected_data["categories"]
        assert actual_instance.exclude_from_games == expected_data["excludeFromGames"]
        assert actual_instance.exclude_from_kids == expected_data["excludeFromKids"]

        acknowledgements = Acknowledgement.objects.filter(
            dictionary_entry=actual_instance
        )
        assert len(acknowledgements) == len(expected_data["acknowledgements"])

        alternate_spellings = AlternateSpelling.objects.filter(
            dictionary_entry=actual_instance
        )
        assert len(alternate_spellings) == len(expected_data["alternateSpellings"])

        notes = Note.objects.filter(dictionary_entry=actual_instance)
        assert len(notes) == len(expected_data["notes"])

        translations = Translation.objects.filter(dictionary_entry=actual_instance)
        assert len(translations) == len(expected_data["translations"])

        pronunciations = Pronunciation.objects.filter(dictionary_entry=actual_instance)
        assert len(pronunciations) == len(expected_data["pronunciations"])

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

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        return self.get_expected_response(instance, instance.site)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def get_expected_list_response_item(self, entry, site):
        return self.get_expected_response(entry, site)

    def create_instance_with_media(
        self,
        site,
        visibility,
        related_images=None,
        related_audio=None,
        related_videos=None,
    ):
        return factories.DictionaryEntryFactory.create(
            site=site,
            visibility=visibility,
            related_images=related_images,
            related_audio=related_audio,
            related_videos=related_videos,
        )

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
            "acknowledgements": [],
            "alternateSpellings": [],
            "notes": [],
            "translations": [],
            "partOfSpeech": None,
            "pronunciations": [],
            "relatedDictionaryEntries": [],
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
        }

    def create_original_instance_for_patch(self, site):
        audio = factories.AudioFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)
        category = factories.CategoryFactory.create(site=site)
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=site,
            title="Title",
            type=TypeOfDictionaryEntry.WORD,
            batch_id="Batch ID",
            exclude_from_wotd=True,
            related_audio=(audio,),
            related_images=(image,),
            related_videos=(video,),
        )
        entry_two = factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryLinkFactory.create(
            from_dictionary_entry=dictionary_entry, to_dictionary_entry=entry_two
        )
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
        assert updated_instance.batch_id == original_instance.batch_id
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

    @pytest.mark.django_db
    def test_list_permissions(self):
        # create some visible words and some invisible words
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)
        factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.MEMBERS
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["count"] == 1, "did not filter out blocked sites"
        assert len(response_data["results"]) == 1, "did not include available site"

    @pytest.mark.parametrize(
        "field",
        [
            {
                "factory": factories.AlternateSpellingFactory,
                "name": "alternateSpellings",
            },
            {"factory": factories.AcknowledgementFactory, "name": "acknowledgements"},
            {"factory": factories.NoteFactory, "name": "notes"},
            {"factory": factories.PronunciationFactory, "name": "pronunciations"},
        ],
        ids=["alternateSpellings", "acknowledgements", "notes", "pronunciations"],
    )
    @pytest.mark.django_db
    def test_detail_fields(self, field):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)

        text = "bon mots"
        model = field["factory"].create(dictionary_entry=entry, text=text)

        response = self.client.get(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data[field["name"]] == [
            {"id": str(model.id), "text": f"{text}"}
        ]

    @pytest.mark.django_db
    def test_detail_translations(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)

        text = "bon mots"
        model = factories.TranslationFactory.create(dictionary_entry=entry, text=text)

        response = self.client.get(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["translations"] == [
            {
                "id": str(model.id),
                "text": f"{text}",
            }
        ]

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

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert (
            len(response_data["relatedDictionaryEntries"]) >= 1
        ), "Did not include related entry"
        assert (
            not len(response_data["relatedDictionaryEntries"]) > 1
        ), "Did not block private related entry"
        assert response_data["relatedDictionaryEntries"] == [
            {
                "id": str(entry2.id),
                "title": entry2.title,
                "url": f"http://testserver/api/1.0/sites/{site.slug}/dictionary/{str(entry2.id)}",
                "translations": [],
                "relatedImages": [],
                "relatedAudio": [],
                "relatedVideos": [],
                "type": entry2.type,
            }
        ]

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
    def test_character_lists_generation(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")

        factories.AlphabetFactory.create(site=site)

        factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, title="bc a"
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_character_lists_generation_with_variants(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        factories.CharacterFactory.create(site=site, title="x")
        factories.CharacterFactory.create(site=site, title="y")
        factories.CharacterFactory.create(site=site, title="c")
        aa = factories.CharacterFactory.create(site=site, title="aa")
        h = factories.CharacterFactory.create(site=site, title="h")
        ch = factories.CharacterFactory.create(site=site, title="ch")

        factories.CharacterVariantFactory.create(
            site=site, title="AA", base_character=aa
        )
        factories.CharacterVariantFactory.create(
            site=site, title="Ch", base_character=ch
        )
        factories.CharacterVariantFactory.create(site=site, title="H", base_character=h)

        factories.AlphabetFactory.create(site=site)

        factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, title="ChxyAA hcH"
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_character_lists_unrecognized_characters(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, title="abc"
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_character_lists_with_ignored_characters(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        factories.CharacterFactory.create(site=site, title="x")
        factories.CharacterFactory.create(site=site, title="y")
        factories.IgnoredCharacterFactory.create(site=site, title="&")

        factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, title="x&y"
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_character_lists_ignored_character_edge_case(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        factories.CharacterFactory.create(site=site, title="x-")
        factories.CharacterFactory.create(site=site, title="y")
        factories.IgnoredCharacterFactory.create(site=site, title="-")

        factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, title="x-y"
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_word_lists(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")

        factories.AlphabetFactory.create(site=site)

        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            title="abc bca caba",
            type=TypeOfDictionaryEntry.PHRASE,
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_word_lists_with_variants(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        factories.CharacterFactory.create(site=site, title="x")
        char = factories.CharacterFactory.create(site=site, title="y")
        factories.CharacterVariantFactory.create(
            site=site, title="Y", base_character=char
        )

        factories.AlphabetFactory.create(site=site)

        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            title="xyY yYx xYy",
            type=TypeOfDictionaryEntry.PHRASE,
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_word_lists_single_word(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")

        factories.AlphabetFactory.create(site=site)

        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            title="abc",
            type=TypeOfDictionaryEntry.PHRASE,
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_word_lists_with_unknown_characters(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        factories.CharacterFactory.create(site=site, title="x")
        y = factories.CharacterFactory.create(site=site, title="y")
        factories.CharacterVariantFactory.create(site=site, title="Y", base_character=y)

        factories.AlphabetFactory.create(site=site)

        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            title="xyY yYx xYy Hello",
            type=TypeOfDictionaryEntry.PHRASE,
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_word_lists_with_ignored_characters(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        factories.CharacterFactory.create(site=site, title="x")
        factories.CharacterFactory.create(site=site, title="y")
        factories.IgnoredCharacterFactory.create(site=site, title="-")

        factories.AlphabetFactory.create(site=site)

        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            title="xy-y -y-x x-y-",
            type=TypeOfDictionaryEntry.PHRASE,
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

    @pytest.mark.django_db
    def test_dictionary_entry_create_no_content(self):
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory()
        data = {}

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_dictionary_entry_create(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        factories.AlphabetFactory.create(site=site)
        category = factories.CategoryFactory.create(site=site)
        part_of_speech = factories.PartOfSpeechFactory.create()
        related_entry = factories.DictionaryEntryFactory.create(site=site)

        data = {
            "title": "Hello",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "team",
            "categories": [str(category.id)],
            "exclude_from_games": False,
            "exclude_from_kids": False,
            "acknowledgements": [{"text": "Thank"}, {"text": "You"}],
            "alternate_spellings": [{"text": "Hello"}, {"text": "World"}],
            "notes": [{"text": self.NOTE_TEXT}, {"text": "Note 2"}],
            "translations": [{"text": "Hallo"}],
            "part_of_speech": str(part_of_speech.id),
            "pronunciations": [{"text": "Huh-lo"}],
            "related_dictionary_entries": [str(related_entry.id)],
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        # Test API response
        response_data = json.loads(response.content)
        assert response_data["title"] == "Hello"
        assert response_data["type"] == TypeOfDictionaryEntry.WORD
        assert response_data["visibility"] == "team"
        assert response_data["categories"][0]["id"] == str(category.id)
        assert response_data["excludeFromGames"] is False
        assert response_data["excludeFromKids"] is False
        assert response_data["acknowledgements"][0]["text"] == "Thank"
        assert response_data["acknowledgements"][1]["text"] == "You"
        assert response_data["alternateSpellings"][0]["text"] == "Hello"
        assert response_data["alternateSpellings"][1]["text"] == "World"
        assert response_data["notes"][0]["text"] == self.NOTE_TEXT
        assert response_data["notes"][1]["text"] == "Note 2"
        assert response_data["translations"][0]["text"] == "Hallo"
        assert response_data["partOfSpeech"]["id"] == str(part_of_speech.id)
        assert response_data["pronunciations"][0]["text"] == "Huh-lo"
        assert response_data["relatedDictionaryEntries"][0]["id"] == str(
            related_entry.id
        )

        # Test DB changes
        entry_in_db = DictionaryEntry.objects.get(id=response_data["id"])
        assert entry_in_db.title == "Hello"
        assert entry_in_db.type == TypeOfDictionaryEntry.WORD
        assert entry_in_db.visibility == Visibility.TEAM
        assert entry_in_db.categories.first().id == category.id
        assert entry_in_db.exclude_from_games is False
        assert entry_in_db.exclude_from_kids is False
        assert entry_in_db.part_of_speech.id == part_of_speech.id

        acknowledgements = Acknowledgement.objects.filter(dictionary_entry=entry_in_db)
        assert acknowledgements.count() == 2

        alternate_spellings = AlternateSpelling.objects.filter(
            dictionary_entry=entry_in_db
        )
        assert alternate_spellings.count() == 2

        notes = Note.objects.filter(dictionary_entry=entry_in_db)
        assert notes.count() == 2

        translations = Translation.objects.filter(dictionary_entry=entry_in_db)
        assert translations.count() == 1
        assert translations.first().text == "Hallo"

        pronunciations = Pronunciation.objects.filter(dictionary_entry=entry_in_db)
        assert pronunciations.count() == 1
        assert pronunciations.first().text == "Huh-lo"

        assert entry_in_db.related_dictionary_entries.first().id == related_entry.id

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

    @pytest.mark.django_db
    def test_dictionary_entry_create_related_media(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        factories.AlphabetFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)

        data = {
            "title": "Hello",
            "type": TypeOfDictionaryEntry.WORD,
            "visibility": "public",
            "exclude_from_games": False,
            "exclude_from_kids": False,
            "related_audio": [str(audio.id)],
            "related_images": [str(image.id)],
            "related_videos": [str(video.id)],
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        # Test API response
        response_data = json.loads(response.content)
        assert response_data["relatedAudio"][0]["id"] == str(audio.id)
        assert response_data["relatedImages"][0]["id"] == str(image.id)
        assert response_data["relatedVideos"][0]["id"] == str(video.id)

        # Test DB changes
        entry_in_db = DictionaryEntry.objects.get(id=response_data["id"])
        assert entry_in_db.related_audio.first().id == audio.id
        assert entry_in_db.related_images.first().id == image.id
        assert entry_in_db.related_videos.first().id == video.id

    @pytest.mark.django_db
    def test_dictionary_entry_create_invalid_related_media(self):
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
            "related_audio": [1234],
            "related_images": [1234],
            "related_videos": [1234],
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_dictionary_entry_update(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        factories.AlphabetFactory.create(site=site)
        category = factories.CategoryFactory.create(site=site)
        part_of_speech = factories.PartOfSpeechFactory.create()
        related_entry = factories.DictionaryEntryFactory.create(site=site)

        entry = factories.DictionaryEntryFactory.create(
            site=site,
            title="Hello",
            type=TypeOfDictionaryEntry.WORD,
            visibility=Visibility.PUBLIC,
            exclude_from_games=False,
            exclude_from_kids=False,
        )

        data = {
            "title": "Goodbye",
            "type": TypeOfDictionaryEntry.PHRASE,
            "visibility": "team",
            "categories": [str(category.id)],
            "exclude_from_games": True,
            "exclude_from_kids": True,
            "acknowledgements": [{"text": "Thanks"}],
            "alternate_spellings": [{"text": "Gooodbye"}],
            "notes": [{"text": self.NOTE_TEXT}],
            "translations": [{"text": self.TRANSLATION_TEXT}],
            "part_of_speech": str(part_of_speech.id),
            "pronunciations": [{"text": "Good-bye"}],
            "related_dictionary_entries": [str(related_entry.id)],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        # Test API response
        response_data = json.loads(response.content)
        assert response_data["title"] == "Goodbye"
        assert response_data["type"] == TypeOfDictionaryEntry.PHRASE
        assert response_data["visibility"] == "team"
        assert response_data["categories"][0]["id"] == str(category.id)
        assert response_data["excludeFromGames"] is True
        assert response_data["excludeFromKids"] is True
        assert response_data["acknowledgements"][0]["text"] == "Thanks"
        assert response_data["alternateSpellings"][0]["text"] == "Gooodbye"
        assert response_data["notes"][0]["text"] == self.NOTE_TEXT
        assert response_data["translations"][0]["text"] == self.TRANSLATION_TEXT
        assert response_data["partOfSpeech"]["id"] == str(part_of_speech.id)
        assert response_data["pronunciations"][0]["text"] == "Good-bye"
        assert response_data["relatedDictionaryEntries"][0]["id"] == str(
            related_entry.id
        )

        # Test DB changes
        entry_in_db = DictionaryEntry.objects.get(id=response_data["id"])
        assert entry_in_db.title == "Goodbye"
        assert entry_in_db.type == TypeOfDictionaryEntry.PHRASE
        assert entry_in_db.visibility == Visibility.TEAM
        assert entry_in_db.categories.first().id == category.id
        assert entry_in_db.exclude_from_games is True
        assert entry_in_db.exclude_from_kids is True
        assert entry_in_db.part_of_speech.id == part_of_speech.id

        acknowledgements = Acknowledgement.objects.filter(dictionary_entry=entry_in_db)
        assert acknowledgements.count() == 1
        assert acknowledgements.first().text == "Thanks"

        alternate_spellings = AlternateSpelling.objects.filter(
            dictionary_entry=entry_in_db
        )
        assert alternate_spellings.count() == 1
        assert alternate_spellings.first().text == "Gooodbye"

        notes = Note.objects.filter(dictionary_entry=entry_in_db)
        assert notes.count() == 1
        assert notes.first().text == self.NOTE_TEXT

        translations = Translation.objects.filter(dictionary_entry=entry_in_db)
        assert translations.count() == 1
        assert translations.first().text == self.TRANSLATION_TEXT

        pronunciations = Pronunciation.objects.filter(dictionary_entry=entry_in_db)
        assert pronunciations.count() == 1
        assert pronunciations.first().text == "Good-bye"

        assert entry_in_db.related_dictionary_entries.first().id == related_entry.id

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

    @pytest.mark.django_db
    def test_dictionary_entry_update_no_content(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(
            site=site,
            title="Hello",
            type=TypeOfDictionaryEntry.WORD,
            visibility=Visibility.PUBLIC,
            exclude_from_games=False,
            exclude_from_kids=False,
        )

        data = {}

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_dictionary_entry_update_related_media(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)

        data = {
            "title": "Goodbye",
            "type": TypeOfDictionaryEntry.PHRASE,
            "visibility": "team",
            "exclude_from_games": True,
            "exclude_from_kids": True,
            "related_audio": [str(audio.id)],
            "related_images": [str(image.id)],
            "related_videos": [str(video.id)],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        response_data = response.json()
        assert response_data["relatedAudio"][0]["id"] == str(audio.id)
        assert response_data["relatedImages"][0]["id"] == str(image.id)
        assert response_data["relatedVideos"][0]["id"] == str(video.id)

        entry_in_db = DictionaryEntry.objects.get(id=response_data["id"])
        assert entry_in_db.related_audio.first().id == audio.id
        assert entry_in_db.related_images.first().id == image.id
        assert entry_in_db.related_videos.first().id == video.id

    @pytest.mark.django_db
    def test_dictionary_entry_update_invalid_related_media(self):
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
            "related_audio": ["1234"],
            "related_images": ["1234"],
            "related_videos": ["1234"],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_dictionary_entry_same_site_validation(self):
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
    def test_dictionary_entry_delete(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)

        response = self.client.delete(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )

        assert response.status_code == 204
        assert DictionaryEntry.objects.filter(id=entry.id).exists() is False

    @pytest.mark.django_db
    def test_dictionary_entry_delete_related_objects(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.EDITOR
        )
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site)
        factories.AcknowledgementFactory.create(dictionary_entry=entry)
        factories.AlternateSpellingFactory.create(dictionary_entry=entry)
        factories.NoteFactory.create(dictionary_entry=entry)
        factories.TranslationFactory.create(dictionary_entry=entry)
        factories.PronunciationFactory.create(dictionary_entry=entry)

        response = self.client.delete(
            self.get_detail_endpoint(key=entry.id, site_slug=site.slug)
        )

        assert response.status_code == 204
        assert DictionaryEntry.objects.filter(id=entry.id).exists() is False
        assert Acknowledgement.objects.filter(dictionary_entry=entry).exists() is False
        assert (
            AlternateSpelling.objects.filter(dictionary_entry=entry).exists() is False
        )
        assert Note.objects.filter(dictionary_entry=entry).exists() is False
        assert Translation.objects.filter(dictionary_entry=entry).exists() is False
        assert Pronunciation.objects.filter(dictionary_entry=entry).exists() is False

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
