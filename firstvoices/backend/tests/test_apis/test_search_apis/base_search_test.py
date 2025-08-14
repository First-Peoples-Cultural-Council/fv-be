import uuid
from unittest.mock import MagicMock

import pytest
from elasticsearch.dsl import Search

from backend.pagination import SearchPageNumberPagination


class SearchMocksMixin:
    """
    Mocking for search operations.
    """

    @pytest.fixture
    def mock_get_page_size(self, mocker):
        return mocker.patch.object(
            SearchPageNumberPagination, "get_page_size", new_callable=MagicMock
        )

    @pytest.fixture
    def mock_search_query_execute(self, mocker):
        return mocker.patch.object(Search, "execute", new_callable=MagicMock)

    def create_mock_request(self, user, query_dict):
        mock_request = MagicMock()
        mock_request.user = user
        mock_request.GET = query_dict
        mock_request.query_params = query_dict
        return mock_request

    def get_search_result(self, index_name, model, document_type):
        model_id = str(model.id) if model else str(uuid.uuid4())
        return {
            "_index": index_name,
            "_type": "_doc",
            "_id": "result_" + model_id,
            "_score": None,
            "_source": {
                "document_id": model_id,
                "document_type": document_type,
            },
        }

    def get_song_search_result(self, song=None):
        return self.get_search_result("songs_2024_01_25_00_03_01", song, "Song")

    def get_story_search_result(self, story=None):
        return self.get_search_result("stories_2024_01_25_00_03_01", story, "Story")

    def get_image_search_result(self, image=None):
        return self.get_search_result("media_2024_01_25_00_03_01", image, "Image")

    def get_audio_search_result(self, audio=None):
        return self.get_search_result("media_2024_01_25_00_03_01", audio, "Audio")

    def get_video_search_result(self, video=None):
        return self.get_search_result("media_2024_01_25_00_03_01", video, "Video")

    def get_document_search_result(self, document=None):
        return self.get_search_result("media_2024_01_25_00_03_01", document, "Document")

    def get_dictionary_search_result(self, dictionary_entry=None):
        return self.get_search_result(
            "dictionary_entries_2024_01_25_00_03_01",
            dictionary_entry,
            "DictionaryEntry",
        )
