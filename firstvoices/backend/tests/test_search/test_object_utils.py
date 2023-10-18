from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl import Search

from backend.models import DictionaryEntry, Song
from backend.models.constants import Visibility
from backend.search.utils.object_utils import (
    get_acknowledgements_text,
    get_categories_ids,
    get_lyrics,
    get_notes_text,
    get_object_from_index,
    get_translation_text,
)
from backend.tests import factories


class TestGetObjectFromIndex:
    # Checking if the error cases are raised correctly
    # The method relies on ES to find and return the correct object which we are not testing

    @pytest.fixture
    def mock_search_query_execute(self, mocker):
        mock_execute = mocker.patch.object(Search, "execute", new_callable=MagicMock)

        return mock_execute

    def test_successful_search(self, mock_search_query_execute):
        mock_es_results = {
            "hits": {
                "hits": [
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_type": "_doc",
                        "_id": "PcHg5ogB3WiEloeO9rdy",
                        "_score": 1.0,
                        "_source": {
                            "document_id": "0101",
                            "site_id": "1234",
                            "title": "bb",
                            "type": "word",
                            "translation": "",
                            "part_of_speech": "",
                            "note": "",
                            "custom_order": "##",
                        },
                        "sort": [1.0, "##"],
                    },
                ],
                "total": {"value": 1, "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_es_results

        test_index = "test_index"
        document_type = "dictionary_entry"
        document_id = "0101"

        result = get_object_from_index(test_index, document_type, document_id)

        assert result is not None
        assert result["_source"]["document_id"] == document_id

    def test_no_search_results(self, mock_search_query_execute):
        mock_es_results = {
            "hits": {
                "hits": [],
                "total": {"value": 0, "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_es_results

        test_index = "test_index"
        document_type = "dictionary_entry"
        document_id = "0101"

        result = get_object_from_index(test_index, document_type, document_id)

        assert result is None

    @pytest.mark.skip(reason="Cannot emulate the connection error.")
    def test_connection_error(self):
        # Skipping as could not emulate the connection error. ES client always raises the connection timeout
        # error before the mocked connection error occurs.
        pass

    @pytest.mark.skip(reason="Cannot emulate the not found error")
    def test_not_found_error(self):
        # Skipping as could not emulate the not found error.
        pass


@pytest.mark.django_db
class TestGetTranslationText:
    def test_no_translation(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_translation_text(dictionary_entry) == ""

    def test_basic_case(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        translation_text = "coffee"
        factories.TranslationFactory.create(
            dictionary_entry=entry, text=translation_text
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_translation_text(dictionary_entry) == translation_text

    def test_multiple_translations(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        translation_text_1 = "coffee"
        factories.TranslationFactory.create(
            dictionary_entry=entry, text=translation_text_1
        )
        translation_text_2 = "tea"
        factories.TranslationFactory.create(
            dictionary_entry=entry, text=translation_text_2
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert (
            get_translation_text(dictionary_entry)
            == f"{translation_text_1} {translation_text_2}"
        )


@pytest.mark.django_db
class TestGetAcknowledgementsText:
    def test_no_acknowledgement(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_acknowledgements_text(dictionary_entry) == ""

    def test_basic_case(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        acknowledgement_text = "coffee"
        factories.AcknowledgementFactory.create(
            dictionary_entry=entry, text=acknowledgement_text
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_acknowledgements_text(dictionary_entry) == acknowledgement_text

    def test_multiple_acknowledgements(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        acknowledgement_text_1 = "coffee"
        factories.AcknowledgementFactory.create(
            dictionary_entry=entry, text=acknowledgement_text_1
        )
        acknowledgement_text_2 = "tea"
        factories.AcknowledgementFactory.create(
            dictionary_entry=entry, text=acknowledgement_text_2
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert (
            get_acknowledgements_text(dictionary_entry)
            == f"{acknowledgement_text_1} {acknowledgement_text_2}"
        )


@pytest.mark.django_db
class TestGetNotesText:
    def test_no_notes(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_notes_text(dictionary_entry) == ""

    def test_basic_case(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        notes_text = "coffee"
        factories.NoteFactory.create(dictionary_entry=entry, text=notes_text)

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_notes_text(dictionary_entry) == notes_text

    def test_multiple_notes(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        note_text_1 = "coffee"
        factories.AcknowledgementFactory.create(
            dictionary_entry=entry, text=note_text_1
        )
        note_text_2 = "tea"
        factories.AcknowledgementFactory.create(
            dictionary_entry=entry, text=note_text_2
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert (
            get_acknowledgements_text(dictionary_entry)
            == f"{note_text_1} {note_text_2}"
        )


@pytest.mark.django_db
class TestGetCategoryIds:
    def test_no_categories(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_categories_ids(dictionary_entry) == []

    def test_basic_case(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        category = factories.CategoryFactory.create(site=site)
        entry.categories.add(category)

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_categories_ids(dictionary_entry) == [str(category.id)]

    def test_multiple_categories(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        category_1 = factories.CategoryFactory.create(site=site)
        category_2 = factories.CategoryFactory.create(site=site)
        entry.categories.add(category_1)
        entry.categories.add(category_2)

        dictionary_entry = DictionaryEntry.objects.get(id=entry.id)
        assert get_categories_ids(dictionary_entry) == [
            str(category_1.id),
            str(category_2.id),
        ]


@pytest.mark.django_db
class TestGetLyrics:
    def test_no_lyrics(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        song = Song.objects.get(id=entry.id)
        actual_lyrics, actual_lyrics_translation = get_lyrics(song)
        assert actual_lyrics == []
        assert actual_lyrics_translation == []

    def test_basic_case(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        lyrics_text = "mocha"
        lyrics_translation_text = "coffee"
        factories.LyricsFactory.create(
            text=lyrics_text, translation=lyrics_translation_text, song=entry
        )

        song = Song.objects.get(id=entry.id)
        actual_lyrics, actual_lyrics_translation = get_lyrics(song)
        assert actual_lyrics == [lyrics_text]
        assert actual_lyrics_translation == [lyrics_translation_text]

    def test_multiple_lyrics(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        lyrics_text_1 = "mocha"
        lyrics_translation_text_1 = "coffee"
        factories.LyricsFactory.create(
            text=lyrics_text_1, translation=lyrics_translation_text_1, song=entry
        )
        lyrics_text_2 = "london fog"
        lyrics_translation_text_2 = "tea"
        factories.LyricsFactory.create(
            text=lyrics_text_2, translation=lyrics_translation_text_2, song=entry
        )

        song = Song.objects.get(id=entry.id)
        actual_lyrics, actual_lyrics_translation = get_lyrics(song)
        assert actual_lyrics == [lyrics_text_1, lyrics_text_2]
        assert actual_lyrics_translation == [
            lyrics_translation_text_1,
            lyrics_translation_text_2,
        ]
