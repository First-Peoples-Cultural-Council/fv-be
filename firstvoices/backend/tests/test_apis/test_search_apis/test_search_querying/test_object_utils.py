import logging
from unittest.mock import MagicMock, patch

import pytest
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Search

from backend.models import DictionaryEntry
from backend.models.constants import Visibility
from backend.search.utils.object_utils import get_categories_ids, get_object_from_index
from backend.tests import factories


class TestGetObjectFromIndex:
    # Checking if the error cases are raised correctly
    # The method relies on ES to find and return the correct object which we are not testing

    @pytest.fixture
    def mock_search_query_execute(self, mocker):
        mock_execute = mocker.patch.object(Search, "execute", new_callable=MagicMock)

        return mock_execute

    class ConnectionError(ConnectionError):
        @property
        def error(self):
            return "Connection Error"

        @property
        def info(self):
            return "Simulated connection error"

    class NotFoundError(NotFoundError):
        @property
        def status_code(self):
            return 404

        @property
        def error(self):
            return "Not found exception"

        @property
        def info(self):
            return "Simulated not found exception"

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

    def test_connection_error(self, caplog):
        test_index = "test_index"
        document_type = "dictionary_entry"
        document_id = "0101"

        with patch(
            "elasticsearch_dsl.Search.execute", side_effect=self.ConnectionError()
        ):
            with pytest.raises(ConnectionError):
                get_object_from_index(test_index, document_type, document_id)
            assert "Elasticsearch server down." in caplog.text
            assert document_type in caplog.text
            assert document_id in caplog.text

    def test_not_found_error(self, caplog):
        caplog.set_level(logging.WARNING)

        test_index = "test_index"
        document_type = "dictionary_entry"
        document_id = "0101"

        with patch(
            "elasticsearch_dsl.Search.execute", side_effect=self.NotFoundError()
        ):
            get_object_from_index(test_index, document_type, document_id)
            assert "Indexed document not found." in caplog.text
            assert test_index in caplog.text
            assert document_id in caplog.text


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
