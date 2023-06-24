import json
from unittest.mock import MagicMock, patch

import pytest
from elasticsearch_dsl import Search

from backend.models.constants import AppRole, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories

from .base_api_test import BaseApiTest


class TestSearchAPI(BaseApiTest):
    """Tests for base search views."""

    API_LIST_VIEW = "api:search-list"
    API_DETAIL_VIEW = "api:search-detail"

    @pytest.fixture
    def mock_search_query_execute(self, mocker):
        mock_search = Search

        mock_execute = mocker.patch.object(
            mock_search, "execute", new_callable=MagicMock
        )

        return mock_execute

    @patch("backend.search.utils.constants.ES_PAGE_SIZE", 1)
    @pytest.mark.django_db
    def test_search_pagination(self, db, mock_search_query_execute):
        """Test that the pagination works as expected."""
        # FIXME: Patch works in class scope but not full suite??
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)
        factories.CharacterFactory.create(site=site, title="a", sort_order=1)
        factories.CharacterFactory.create(site=site, title="b", sort_order=2)
        factories.CharacterFactory.create(site=site, title="c", sort_order=3)

        entry1 = factories.DictionaryEntryFactory.create(site=site, title="aa")
        entry2 = factories.DictionaryEntryFactory.create(site=site, title="bb")
        entry3 = factories.DictionaryEntryFactory.create(site=site, title="cc")

        # Create a mock response
        mock_es_results = {
            "hits": {
                "hits": [
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_type": "_doc",
                        "_id": "QcHg5ogB3WiEloeO9rdy",
                        "_score": 1.0,
                        "_source": {
                            "document_id": entry1.id,
                            "site_id": site.id,
                            "title": "aa",
                            "type": TypeOfDictionaryEntry.WORD,
                            "translation": "",
                            "part_of_speech": "",
                            "note": "",
                            "custom_order": "!!",
                        },
                        "sort": [1.0, "!!"],
                    },
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_type": "_doc",
                        "_id": "PcHg5ogB3WiEloeO9rdy",
                        "_score": 1.0,
                        "_source": {
                            "document_id": entry2.id,
                            "site_id": site.id,
                            "title": "bb",
                            "type": TypeOfDictionaryEntry.WORD,
                            "translation": "",
                            "part_of_speech": "",
                            "note": "",
                            "custom_order": "##",
                        },
                        "sort": [1.0, "##"],
                    },
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_type": "_doc",
                        "_id": "RcHg5ogB3WiEloeO9rdy",
                        "_score": 1.0,
                        "_source": {
                            "document_id": entry3.id,
                            "site_id": site.id,
                            "title": "cc",
                            "type": TypeOfDictionaryEntry.WORD,
                            "translation": "",
                            "part_of_speech": "",
                            "note": "",
                            "custom_order": "$$",
                        },
                        "sort": [1.0, "$$"],
                    },
                ],
                "total": {"value": 3, "relation": "eq"},
            }
        }

        mock_search_query_execute.return_value = mock_es_results

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint() + "?page=1")
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 3
        assert response_data["pages"] == 3
        assert response_data["pageSize"] == 1
        assert response_data["next"] == 2
        assert response_data["nextUrl"] == "http://testserver/api/1.0/search?page=2"
        assert response_data["previous"] is None
        assert response_data["previousUrl"] is None

        response = self.client.get(response_data["nextUrl"])
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 3
        assert response_data["pages"] == 3
        assert response_data["pageSize"] == 1
        assert response_data["next"] == 3
        assert response_data["nextUrl"] == "http://testserver/api/1.0/search?page=3"
        assert response_data["previous"] == 1
        assert response_data["previousUrl"] == "http://testserver/api/1.0/search"

        response = self.client.get(response_data["nextUrl"])
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 3
        assert response_data["pages"] == 3
        assert response_data["pageSize"] == 1
        assert response_data["next"] is None
        assert response_data["nextUrl"] is None
        assert response_data["previous"] == 2
        assert response_data["previousUrl"] == "http://testserver/api/1.0/search?page=2"
