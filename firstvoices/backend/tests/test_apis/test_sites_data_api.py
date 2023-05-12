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
        response_data = json.loads(response.content)[0]

        config = response_data["siteDataExport"]["config"]
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

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)[0]

        config = response_data["siteDataExport"]["config"]
        assert config["L1"] == {
            "name": site.title,
            "lettersInLanguage": [char_a.title, char_b.title, char_c.title],
            "transducers": {},
        }
        assert config["L2"] == {"name": "English"}
        assert self.is_time_format(config["build"])

    @pytest.mark.django_db
    def test_dictionary_empty(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)[0]

        dictionary_entries = response_data["siteDataExport"]["data"]
        assert len(dictionary_entries) == 0

    @pytest.mark.django_db
    def test_dictionary_entries(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title="title_one",
        )
        entry_two = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="title_two",
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)[0]

        dictionary_entries = response_data["siteDataExport"]["data"]
        assert len(dictionary_entries) == 2

        assert dictionary_entries[0] == {
            "source": "words",
            "entryID": str(entry_one.id),
            "word": entry_one.title,
            "definition": None,
            "audio": [
                {
                    "speaker": None,
                    "filename": "https://v2.dev.firstvoices.com/nuxeo/nxfile/default/136e1a0a-a707-41a9-9ec8"
                    "-1a4f05b55454/file:content/TestMP3.mp3",
                }
            ],
            "img": "https://v2.dev.firstvoices.com/nuxeo/nxfile/default/5c9eef16-4665-40b9-89ce-debc0301f93b/file"
            ":content/pexels-stijn-dijkstra-2583852.jpg",
            "theme": [],
            "secondary_theme": None,
            "optional": [{}],
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
            "audio": [
                {
                    "speaker": None,
                    "filename": "https://v2.dev.firstvoices.com/nuxeo/nxfile/default/136e1a0a-a707-41a9-9ec8"
                    "-1a4f05b55454/file:content/TestMP3.mp3",
                }
            ],
            "img": "https://v2.dev.firstvoices.com/nuxeo/nxfile/default/5c9eef16-4665-40b9-89ce-debc0301f93b/file"
            ":content/pexels-stijn-dijkstra-2583852.jpg",
            "theme": [],
            "secondary_theme": None,
            "optional": [{}],
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
        response_data = json.loads(response.content)[0]

        dictionary_entries = response_data["siteDataExport"]["data"]
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
        DictionaryEntryCategoryFactory(category=category3, dictionary_entry=entry_two)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)[0]

        dictionary_entries = response_data["siteDataExport"]["data"]
        assert len(dictionary_entries) == 2

        assert dictionary_entries[0]["theme"] == [
            {"category": category1.title, "parent_category": None}
        ]
        assert len(dictionary_entries[0]["theme"]) == 1

        assert dictionary_entries[1]["theme"] == [
            {"category": category3.title, "parent_category": category2.title}
        ]
        assert len(dictionary_entries[1]["theme"]) == 1

    @pytest.mark.django_db
    def test_dictionary_entries_optional(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
        )

        acknowledgement = AcknowledgementFactory.create(
            dictionary_entry=entry_one, text="test acknowledgement"
        )
        p1 = PartOfSpeech(
            title="part_of_speech_1",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=self.user,
            last_modified_by=self.user,
        )
        p1.save()
        translation = TranslationFactory.create(
            dictionary_entry=entry_one, part_of_speech=p1
        )
        note = NoteFactory.create(dictionary_entry=entry_one, text="test note")

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)[0]

        dictionary_entries = response_data["siteDataExport"]["data"]
        assert len(dictionary_entries) == 1

        assert dictionary_entries[0]["optional"] == [
            {
                "Reference": acknowledgement.text,
                "Part of Speech": translation.part_of_speech.title,
                "Note": note.text,
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
        response_data = json.loads(response.content)[0]

        dictionary_entries = response_data["siteDataExport"]["data"]
        assert len(dictionary_entries) == 1

        assert dictionary_entries[0]["compare_form"] == entry_one.title
        assert dictionary_entries[0]["sort_form"] == "abc"
        assert dictionary_entries[0]["sorting_form"] == [1, 2, 3]
