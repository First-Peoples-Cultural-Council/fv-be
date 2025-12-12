from unittest.mock import MagicMock

import pytest

from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.tests.test_apis.test_search_apis.base_search_test import SearchMocksMixin
from backend.views.base_search_entries_views import BaseSearchEntriesViewSet


class TestBaseSearchViewSet(SearchMocksMixin):
    @pytest.mark.django_db
    @pytest.mark.skip(
        reason="Need to test that author fields are only present to assistants and higher of the same site"
    )
    def test_serialized_entries_have_author_fields(self):
        image = factories.ImageFactory.create()
        audio = factories.AudioFactory.create()
        video = factories.VideoFactory.create()
        document = factories.DocumentFactory.create()
        song = factories.SongFactory.create()
        story = factories.StoryFactory.create()
        word = factories.DictionaryEntryFactory.create(type=TypeOfDictionaryEntry.WORD)

        mock_search_results = [
            self.get_image_search_result(image),
            self.get_audio_search_result(audio),
            self.get_video_search_result(video),
            self.get_document_search_result(document),
            self.get_song_search_result(song),
            self.get_story_search_result(story),
            self.get_dictionary_search_result(word),
        ]

        viewset = BaseSearchEntriesViewSet()
        viewset.request = MagicMock()
        viewset.format_kwarg = MagicMock()

        hydrated_data = viewset.hydrate(mock_search_results)
        serialized_data = viewset.serialize_search_results(
            mock_search_results, hydrated_data
        )

        for serialized_entry, original_entry in zip(
            serialized_data, [image, audio, video, document, song, story, word]
        ):
            assert str(serialized_entry["entry"]["created_by"]) == str(
                original_entry.created_by
            )
            assert str(serialized_entry["entry"]["last_modified_by"]) == str(
                original_entry.last_modified_by
            )
