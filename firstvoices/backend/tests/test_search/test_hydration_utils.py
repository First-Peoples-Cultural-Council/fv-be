from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_MEDIA_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
)
from backend.search.utils.hydration_utils import separate_object_ids


class TestSeparateObjectIds:
    TEST_DICTIONARY_ENTRY_INDEX_NAME = "dictionary_entries_2023_10_18_21_45_08"
    TEST_SONGS_INDEX_NAME = "songs_2023_10_18_21_45_08"
    TEST_STORIES_INDEX_NAME = "stories_2023_10_18_21_45_08"
    TEST_MEDIA_INDEX_NAME = "media_2023_10_18_21_45_09"

    def test_basic_separation(self):
        search_results = [
            {
                "_index": self.TEST_DICTIONARY_ENTRY_INDEX_NAME,
                "_source": {"document_id": 1},
            },
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 2}},
            {"_index": self.TEST_STORIES_INDEX_NAME, "_source": {"document_id": 3}},
            {
                "_index": self.TEST_MEDIA_INDEX_NAME,
                "_source": {"document_id": 4, "type": "audio"},
            },
        ]
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [1],
            ELASTICSEARCH_SONG_INDEX: [2],
            ELASTICSEARCH_STORY_INDEX: [3],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [4], "image": [], "video": []},
        }
        assert separate_object_ids(search_results) == expected_output

    def test_different_data_types(self):
        search_results = [
            {
                "_index": self.TEST_MEDIA_INDEX_NAME,
                "_source": {"document_id": 4, "type": "image"},
            },
            {
                "_index": self.TEST_MEDIA_INDEX_NAME,
                "_source": {"document_id": 5, "type": "video"},
            },
            {
                "_index": self.TEST_MEDIA_INDEX_NAME,
                "_source": {"document_id": 6, "type": "audio"},
            },
        ]
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
            ELASTICSEARCH_SONG_INDEX: [],
            ELASTICSEARCH_STORY_INDEX: [],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [6], "image": [4], "video": [5]},
        }
        assert separate_object_ids(search_results) == expected_output

    def test_multiple_objects_from_same_index(self):
        search_results = [
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 13}},
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 14}},
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 15}},
        ]
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
            ELASTICSEARCH_SONG_INDEX: [13, 14, 15],
            ELASTICSEARCH_STORY_INDEX: [],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [], "image": [], "video": []},
        }
        assert separate_object_ids(search_results) == expected_output

    def test_unknown_index(self):
        search_results = [
            {"_index": "unknown_index", "_source": {"document_id": 7}},
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 8}},
        ]
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
            ELASTICSEARCH_SONG_INDEX: [8],
            ELASTICSEARCH_STORY_INDEX: [],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [], "image": [], "video": []},
        }
        assert separate_object_ids(search_results) == expected_output

    def test_empty_input(self):
        search_results = []
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
            ELASTICSEARCH_SONG_INDEX: [],
            ELASTICSEARCH_STORY_INDEX: [],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [], "image": [], "video": []},
        }
        assert separate_object_ids(search_results) == expected_output
