from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl import Search

from backend.search.utils.object_utils import get_object_from_index


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
