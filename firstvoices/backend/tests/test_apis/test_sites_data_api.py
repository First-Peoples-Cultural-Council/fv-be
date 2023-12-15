import json
import time

import pytest
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models import PartOfSpeech
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.tests.factories import (
    AcknowledgementFactory,
    CategoryFactory,
    CharacterFactory,
    CharacterVariantFactory,
    DictionaryEntryCategoryFactory,
    NoteFactory,
    TranslationFactory,
)


class TestSitesDataEndpoint:
    """
    Tests that check the sites-data endpoint for correct formatting and behavior.
    """

    API_LIST_VIEW = "api:data-list"
    APP_NAME = "backend"

    client = None

    optional_constants = {
        "PART_OF_SPEECH": "Part of Speech",
        "REFERENCE": "Reference",
        "NOTE": "Note",
    }

    def get_list_endpoint(self, site_slug):
        return reverse(self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug])

    def setup_method(self):
        self.client = APIClient()
        self.user = factories.get_non_member_user()
        self.client.force_authenticate(user=self.user)

    def is_time_format(self, input):
        try:
            time.strptime(input, "%Y%m%d%H%M")
            return True
        except ValueError:
            return False

    @pytest.mark.django_db
    def test_list_404_site_not_found(self):
        response = self.client.get(self.get_list_endpoint(site_slug="missing-site"))

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_list_403_site_not_visible(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_empty_config(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        config = response_data["config"]
        assert config["L1"] == {
            "name": site.title,
            "lettersInLanguage": [],
            "transducers": {},
        }
        assert config["L2"] == {"name": "English"}
        assert self.is_time_format(config["build"])

    @pytest.mark.django_db
    def test_full_config(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        char_a = CharacterFactory(site=site, title="a")
        char_b = CharacterFactory(site=site, title="b")
        char_c = CharacterFactory(site=site, title="c")

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug), format="json"
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        config = response_data["config"]
        assert config["L1"] == {
            "name": site.title,
            "lettersInLanguage": [char_a.title, char_b.title, char_c.title],
            "transducers": {},
        }
        assert config["L2"] == {"name": "English"}
        assert self.is_time_format(config["build"])

    @pytest.mark.django_db
    def test_empty_categories(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        site.category_set.all().delete()

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        categories = response_data["categories"]
        assert len(categories) == 0

    @pytest.mark.django_db
    def test_full_categories(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        site.category_set.all().delete()

        parent_category = factories.CategoryFactory.create(
            site=site, title="A category"
        )
        child_category = factories.CategoryFactory.create(
            site=site, title="B category", parent=parent_category
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        categories = response_data["categories"]
        assert len(categories) == 2

        assert categories[0] == {
            "category": parent_category.title,
            "parent_category": None,
        }
        assert categories[1] == {
            "category": child_category.title,
            "parent_category": parent_category.title,
        }

    @pytest.mark.django_db
    def test_dictionary_empty(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 0

    @pytest.mark.django_db
    def test_dictionary_entries(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        speaker = factories.PersonFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        factories.AudioSpeakerFactory.create(audio=audio, speaker=speaker)

        image = factories.ImageFactory.create(site=site)

        parent_category = factories.CategoryFactory.create(site=site)
        child_category = factories.CategoryFactory.create(
            site=site, parent=parent_category
        )

        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title="title_one",
            related_audio=[audio],
            related_images=[image],
        )
        factories.DictionaryEntryCategoryFactory.create(
            category=parent_category, dictionary_entry=entry_one
        )
        factories.DictionaryEntryCategoryFactory.create(
            category=child_category, dictionary_entry=entry_one
        )

        entry_two = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="title_two",
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 2

        assert dictionary_entries[0] == {
            "source": "words",
            "entryID": str(entry_one.id),
            "word": entry_one.title,
            "definition": None,
            "audio": [
                {
                    "speaker": speaker.name,
                    "filename": audio.original.content.url,
                }
            ],
            "img": [
                {
                    "filename": image.original.content.url,
                }
            ],
            "theme": [parent_category.title],
            "secondary_theme": [child_category.title],
            "optional": [
                {
                    self.optional_constants[
                        "PART_OF_SPEECH"
                    ]: entry_one.part_of_speech.title
                }
            ],
            "compare_form": entry_one.title,
            "sort_form": entry_one.title,
            "sorting_form": [
                10116,
                10105,
                10116,
                10108,
                10101,
                10095,
                10111,
                10110,
                10101,
            ],
        }
        assert len(dictionary_entries[0]) == 12

        assert dictionary_entries[1] == {
            "source": "phrases",
            "entryID": str(entry_two.id),
            "word": entry_two.title,
            "definition": None,
            "audio": [],
            "img": [],
            "theme": [],
            "secondary_theme": [],
            "optional": [
                {
                    self.optional_constants[
                        "PART_OF_SPEECH"
                    ]: entry_two.part_of_speech.title
                }
            ],
            "compare_form": entry_two.title,
            "sort_form": entry_two.title,
            "sorting_form": [
                10116,
                10105,
                10116,
                10108,
                10101,
                10095,
                10116,
                10119,
                10111,
            ],
        }
        assert len(dictionary_entries[1]) == 12

    @pytest.mark.django_db
    def test_dictionary_entries_definition(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
        )

        translation = TranslationFactory.create(
            dictionary_entry=entry_one, text="test translation"
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 1

        assert dictionary_entries[0]["definition"] == translation.text

    @pytest.mark.django_db
    def test_dictionary_entries_themes(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
        )

        entry_two = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
        )

        category1 = CategoryFactory(site=site, title="test category A")
        DictionaryEntryCategoryFactory(category=category1, dictionary_entry=entry_one)

        category2 = CategoryFactory(site=site, title="test category B")
        category3 = CategoryFactory(
            site=site, title="test category C", parent=category2
        )
        DictionaryEntryCategoryFactory(category=category2, dictionary_entry=entry_two)
        DictionaryEntryCategoryFactory(category=category3, dictionary_entry=entry_two)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 2

        assert dictionary_entries[0]["theme"] == [category1.title]
        assert len(dictionary_entries[0]["theme"]) == 1

        assert dictionary_entries[1]["theme"] == [category2.title]
        assert len(dictionary_entries[1]["theme"]) == 1
        assert dictionary_entries[1]["secondary_theme"] == [category3.title]
        assert len(dictionary_entries[1]["secondary_theme"]) == 1

    @pytest.mark.django_db
    def test_dictionary_entries_optional(self):
        p1 = PartOfSpeech(
            title="part_of_speech_1",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=self.user,
            last_modified_by=self.user,
        )

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            part_of_speech=p1,
        )

        acknowledgement = AcknowledgementFactory.create(
            dictionary_entry=entry_one, text="test acknowledgement"
        )

        p1.save()
        TranslationFactory.create(dictionary_entry=entry_one)
        note = NoteFactory.create(dictionary_entry=entry_one, text="test note")

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 1

        assert dictionary_entries[0]["optional"] == [
            {
                self.optional_constants["REFERENCE"]: acknowledgement.text,
                self.optional_constants[
                    "PART_OF_SPEECH"
                ]: entry_one.part_of_speech.title,
                self.optional_constants["NOTE"]: note.text,
            }
        ]
        assert len(dictionary_entries[0]["optional"][0]) == 3

    @pytest.mark.django_db
    def test_dictionary_entries_form(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        char_a = CharacterFactory(site=site, title="a", sort_order=1)
        CharacterVariantFactory(site=site, title="A", base_character=char_a)
        CharacterFactory(site=site, title="b", sort_order=2)
        CharacterFactory(site=site, title="c", sort_order=3)

        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title="Abc",
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 1

        assert dictionary_entries[0]["compare_form"] == entry_one.title
        assert dictionary_entries[0]["sort_form"] == "abc"
        assert dictionary_entries[0]["sorting_form"] == [1, 2, 3]
