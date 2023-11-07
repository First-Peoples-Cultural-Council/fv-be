import json
from unittest.mock import MagicMock, patch

import pytest
from elasticsearch.exceptions import ConnectionError
from elasticsearch_dsl import Search

from backend.models.constants import AppRole, Role, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.views.exceptions import ElasticSearchConnectionError

from ...pagination import SearchPageNumberPagination
from .base_api_test import BaseApiTest, BaseSiteContentApiTest


class TestSearchAPI(BaseApiTest):
    """Tests for base search views."""

    API_LIST_VIEW = "api:search-list"
    API_DETAIL_VIEW = "api:search-detail"

    @pytest.fixture
    def mock_get_page_size(self, mocker):
        mock_page_size = mocker.patch.object(
            SearchPageNumberPagination, "get_page_size", new_callable=MagicMock
        )
        return mock_page_size

    @pytest.fixture
    def mock_search_query_execute(self, mocker):
        mock_execute = mocker.patch.object(Search, "execute", new_callable=MagicMock)

        return mock_execute

    @pytest.mark.django_db
    def test_search_pagination(self, db, mock_search_query_execute, mock_get_page_size):
        """Test that the pagination works as expected."""

        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)
        factories.CharacterFactory.create(site=site, title="a", sort_order=1)
        factories.CharacterFactory.create(site=site, title="b", sort_order=2)
        factories.CharacterFactory.create(site=site, title="c", sort_order=3)

        entry1 = factories.DictionaryEntryFactory.create(site=site, title="aa")
        entry2 = factories.DictionaryEntryFactory.create(site=site, title="bb")
        entry3 = factories.DictionaryEntryFactory.create(site=site, title="cc")

        mock_get_page_size.return_value = 1

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

    @pytest.mark.django_db
    @pytest.mark.parametrize("page_number", [0, -1, 1.5, "octopus"])
    def test_invalid_page_numbers(self, page_number, db, mock_search_query_execute):
        """Test that invalid page numbers return an invalid page."""
        mock_es_results = {
            "hits": {"hits": [], "total": {"value": 0, "relation": "eq"}},
        }
        mock_search_query_execute.return_value = mock_es_results

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint() + f"?page={page_number}")
        response_data = json.loads(response.content)

        assert response_data == {"detail": "Invalid page."}

    @pytest.mark.django_db
    @pytest.mark.parametrize("page_size", [0, -1, 1.5, "octopus"])
    def test_invalid_page_sizes(self, page_size, db, mock_search_query_execute):
        """Test that invalid page sizes return an expected page with the default page size."""
        mock_es_results = {
            "hits": {"hits": [], "total": {"value": 0, "relation": "eq"}},
        }
        mock_search_query_execute.return_value = mock_es_results

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint() + f"?pageSize={page_size}")
        response_data = json.loads(response.content)

        assert response_data["pageSize"] == 25

    @pytest.mark.django_db
    def test_invalid_types_passed(self):
        response = self.client.get(self.get_list_endpoint() + "?types=cars")
        response_data = json.loads(response.content)

        assert response_data == []

    @pytest.mark.django_db
    def test_invalid_domains_passed(self):
        response = self.client.get(self.get_list_endpoint() + "?domain=creative")
        response_data = json.loads(response.content)

        assert response_data == []

    @pytest.mark.django_db
    def test_connection_error(self, mock_search_query_execute):
        mock_search_query_execute.side_effect = ConnectionError()

        response = self.client.get(self.get_list_endpoint())
        assert response.status_code == 500
        assert (
            response.content.decode()
            == f'{{"detail":"{ElasticSearchConnectionError.default_detail}"}}'
        )

    @pytest.mark.django_db
    def test_without_pagination_response(self, mock_search_query_execute):
        # Improbable scenario, but in case the paginator returns None for a page number,
        # Verifying the response contains a list of objects

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, type=TypeOfDictionaryEntry.WORD
        )

        mock_es_results = {
            "hits": {
                "hits": [
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_id": "QcHg5ogB3WiEloeO9rdy",
                        "_score": 1.0,
                        "_source": {
                            "document_id": entry.id,
                            "site_id": site.id,
                        },
                    }
                ],
                "total": {"value": 1, "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_es_results

        with patch(
            "backend.pagination.SearchPageNumberPagination.apply_search_pagination",
            return_value=None,
        ):
            response = self.client.get(self.get_list_endpoint())
            data = response.data

            assert response.status_code == 200
            assert type(data) is list
            assert (
                data[0]["searchResultId"] == mock_es_results["hits"]["hits"][0]["_id"]
            )
            assert data[0]["entry"]["id"] == str(entry.id)


@pytest.mark.django_db
class TestSiteSearchAPI(BaseSiteContentApiTest):
    """Remaining tests that cover the site search."""

    API_LIST_VIEW = "api:site-search-list"
    API_DETAIL_VIEW = "api:site-search-detail"

    @pytest.fixture
    def mock_search_query_execute(self, mocker):
        mock_execute = mocker.patch.object(Search, "execute", new_callable=MagicMock)

        return mock_execute

    def test_invalid_category_id(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug) + "?category=xyzCategory"
        )
        response_data = json.loads(response.content)

        assert response_data == []

    def test_starts_with_char_param(self, mock_search_query_execute):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, type=TypeOfDictionaryEntry.WORD
        )
        self.client.force_authenticate(user=user)

        mock_es_results = {
            "hits": {
                "hits": [
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_id": "QcHg5ogB3WiEloeO9rdy",
                        "_score": 1.0,
                        "_source": {
                            "document_id": entry.id,
                            "site_id": site.id,
                            "title": "xyz",
                        },
                    }
                ],
                "total": {"value": 1, "relation": "eq"},
            }
        }

        mock_search_query_execute.return_value = mock_es_results

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug) + "?startsWithChar=x"
        )

        assert "startsWithChar=x" in response.request["QUERY_STRING"]
