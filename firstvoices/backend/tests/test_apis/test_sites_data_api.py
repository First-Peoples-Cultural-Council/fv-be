import json
import time

import pytest
from django.utils import timezone
from mothertongues.config.models import DictionaryEntry, LanguageConfiguration
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models import MTDExportFormat, PartOfSpeech
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tasks.build_mtd_export_format import build_index_and_calculate_scores
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
    API_MTD_VIEW = "api:mtd-data-list"
    APP_NAME = "backend"

    client = None

    optional_constants = {
        "PART_OF_SPEECH": "Part of Speech",
        "REFERENCE": "Reference",
        "NOTE": "Note",
    }

    def get_mtd_endpoint(self, site_slug):
        return reverse(self.API_MTD_VIEW, current_app=self.APP_NAME, args=[site_slug])

    def get_list_endpoint(self, site_slug):
        return reverse(self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug])

    def setup_method(self):
        self.client = APIClient()
        self.user = factories.get_non_member_user()
        self.client.force_authenticate(user=self.user)
        self.basic_config = LanguageConfiguration()

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
    def test_no_build_and_score(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        response = self.client.get(self.get_mtd_endpoint(site_slug=site.slug))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_list_403_site_not_visible(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_empty_config(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        # Build after adding entries to site
        build_index_and_calculate_scores(site)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        language_config = LanguageConfiguration(L1=site.title)
        response_config = response_data["config"]
        assert response_config["L1"] == language_config.L1
        assert response_config["L2"] == language_config.L2
        assert self.is_time_format(response_config["build"])

    @pytest.mark.django_db
    def test_full_config(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        char_a = CharacterFactory(site=site, title="a")
        char_b = CharacterFactory(site=site, title="b")
        char_c = CharacterFactory(site=site, title="c")
        # Build after adding characters to site
        build_index_and_calculate_scores(site)

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug), format="json"
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        language_config = LanguageConfiguration(
            L1=site.title, alphabet=[char_a.title, char_b.title, char_c.title]
        )
        response_config = response_data["config"]
        assert response_config["alphabet"] == language_config.alphabet
        assert response_config["L2"] == language_config.L2
        assert self.is_time_format(response_config["build"])

    @pytest.mark.django_db
    def test_dictionary_empty(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        # Build after adding entries to site
        build_index_and_calculate_scores(site)
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

        entry_one_translations = [factories.TranslationFactory.create()]
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

        entry_one.translation_set.set(entry_one_translations)
        entry_two_translations = [factories.TranslationFactory.create()]
        entry_two = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="title_two",
        )
        entry_two.translation_set.set(entry_two_translations)
        # Build after adding entries to site
        build_index_and_calculate_scores(site)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        dictionary_entries = [
            DictionaryEntry(
                word=entry_one.title,
                definition=entry_one.translation_set.first().text,
                entryID=entry_one.id,
                source="words",
                optional={
                    self.optional_constants[
                        "PART_OF_SPEECH"
                    ]: entry_one.part_of_speech.title
                },
            ),
            DictionaryEntry(
                word=entry_two.title,
                definition=entry_two.translation_set.first().text,
                entryID=entry_two.id,
                source="phrases",
                optional={
                    self.optional_constants[
                        "PART_OF_SPEECH"
                    ]: entry_two.part_of_speech.title
                },
            ),
        ]

        response_dictionary_entries = response_data["data"]
        assert len(response_dictionary_entries) == 2

        # The FV backend serializer currently does not return the same format as the MTD export format
        # So we just assert some of the basics here for now.
        assert (
            response_dictionary_entries[0]["definition"]
            == dictionary_entries[0].definition
        )
        assert (
            response_dictionary_entries[0]["entryID"] == dictionary_entries[0].entryID
        )
        assert response_dictionary_entries[0]["word"] == dictionary_entries[0].word
        assert (
            response_dictionary_entries[0]["optional"] == dictionary_entries[0].optional
        )

        assert (
            response_dictionary_entries[1]["definition"]
            == dictionary_entries[1].definition
        )
        assert (
            response_dictionary_entries[1]["entryID"] == dictionary_entries[1].entryID
        )
        assert response_dictionary_entries[1]["word"] == dictionary_entries[1].word
        assert (
            response_dictionary_entries[1]["optional"] == dictionary_entries[1].optional
        )

    @pytest.mark.django_db
    def test_dictionary_entries_with_missing_required_fields(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
        )
        # Build after adding entries to site
        build_index_and_calculate_scores(site)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        dictionary_entries = response_data["data"]
        # If there are missing fields, the basic site data api returns the
        # deficient entries, but they are not stored in the export format
        assert len(dictionary_entries) == 1
        assert dictionary_entries[0]["word"] == entry_one.title
        # For a MTD front-end, every entry must have a definition
        assert dictionary_entries[0]["definition"] is None
        # This entry is therefore excluded from the export format
        export_data = MTDExportFormat.objects.filter(site=site)
        assert len(export_data.first().latest_export_result["data"]) == 0

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
        # Build after adding entries to site
        build_index_and_calculate_scores(site)
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
        TranslationFactory.create(dictionary_entry=entry_one)

        entry_two = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
        )
        TranslationFactory.create(dictionary_entry=entry_two)

        category1 = CategoryFactory(site=site, title="test category A")
        DictionaryEntryCategoryFactory(category=category1, dictionary_entry=entry_one)

        category2 = CategoryFactory(site=site, title="test category B")
        category3 = CategoryFactory(
            site=site, title="test category C", parent=category2
        )
        DictionaryEntryCategoryFactory(category=category2, dictionary_entry=entry_two)
        DictionaryEntryCategoryFactory(category=category3, dictionary_entry=entry_two)
        # Build after adding entries to site
        build_index_and_calculate_scores(site)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 2

        assert dictionary_entries[0]["theme"] == category1.title
        assert dictionary_entries[0]["secondary_theme"] is None

        assert dictionary_entries[1]["theme"] == category2.title
        assert dictionary_entries[1]["secondary_theme"] == category3.title

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
        # Build after adding entries to site
        build_index_and_calculate_scores(site)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 1

        assert dictionary_entries[0]["optional"] == {
            self.optional_constants["REFERENCE"]: acknowledgement.text,
            self.optional_constants["PART_OF_SPEECH"]: entry_one.part_of_speech.title,
            self.optional_constants["NOTE"]: note.text,
        }
        assert len(dictionary_entries[0]["optional"]) == 3

    @pytest.mark.django_db
    def test_dictionary_entries_sort_form(self):
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

        TranslationFactory.create(dictionary_entry=entry_one)
        # Build after adding entries to site
        build_index_and_calculate_scores(site)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        dictionary_entries = response_data["data"]
        assert len(dictionary_entries) == 1
        assert dictionary_entries[0]["sorting_form"] == [1, 2, 3]
