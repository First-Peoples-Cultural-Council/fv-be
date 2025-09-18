import json
from unittest.mock import patch

import pytest
from elasticsearch.exceptions import ConnectionError

from backend.models.constants import AppRole, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.tests.test_apis.base.base_media_test import (
    VIMEO_VIDEO_LINK,
    YOUTUBE_VIDEO_LINK,
)
from backend.tests.test_apis.base.base_non_site_api import (
    BaseNonSiteApiTest,
    NonSiteListEndpointTestMixin,
)
from backend.tests.test_apis.test_search_apis.base_search_test import SearchMocksMixin
from backend.tests.test_apis.test_search_apis.test_search_querying.test_search_entry_results import (
    SearchEntryResultsTestMixin,
)
from backend.views.exceptions import ElasticSearchConnectionError


@pytest.mark.django_db
class TestSearchAPI(
    SearchEntryResultsTestMixin,
    SearchMocksMixin,
    NonSiteListEndpointTestMixin,
    BaseNonSiteApiTest,
):
    """Tests for base search views."""

    API_LIST_VIEW = "api:search-list"

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
                            "document_type": "DictionaryEntry",
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
                            "document_type": "DictionaryEntry",
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
                            "document_type": "DictionaryEntry",
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

    def test_invalid_types_passed(self):
        response = self.client.get(self.get_list_endpoint() + "?types=cars")
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    def test_invalid_domains_passed(self):
        response = self.client.get(self.get_list_endpoint() + "?domain=creative")
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    def test_invalid_visibility(self):
        response = self.client.get(
            self.get_list_endpoint() + "?visibility=invalidVisibility"
        )
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    def test_connection_error(self, mock_search_query_execute):
        mock_search_query_execute.side_effect = ConnectionError("Connection Error.")

        response = self.client.get(self.get_list_endpoint())
        assert response.status_code == 500
        assert (
            response.content.decode()
            == f'{{"detail":"{ElasticSearchConnectionError.default_detail}"}}'
        )

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
                            "document_type": "DictionaryEntry",
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
            data = json.loads(response.content)

            assert response.status_code == 200
            assert type(data) is list
            assert (
                data[0]["searchResultId"] == mock_es_results["hits"]["hits"][0]["_id"]
            )
            assert data[0]["entry"]["id"] == str(entry.id)

    def test_words_length_filter_invalid_combination(self, mock_search_query_execute):
        # Testing out scenario where a invalid combination of max and min words is supplied,
        # i.e. where maxWords < minWords
        response = self.client.get(self.get_list_endpoint() + "?minWords=5&maxWords=2")
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert len(response_data["results"]) == 0

    def test_has_video_param_video_links(self, mock_search_query_execute):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            related_video_links=[YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK],
        )
        song = factories.SongFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            related_video_links=[YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK],
        )
        story = factories.StoryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            related_video_links=[YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK],
        )

        mock_es_results = {
            "hits": {
                "hits": [
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_id": str(entry.id),
                        "_score": 1.0,
                        "_source": {
                            "document_id": entry.id,
                            "document_type": "DictionaryEntry",
                            "site_id": site.id,
                        },
                    },
                    {
                        "_index": "songs_2023_06_23_06_11_22",
                        "_id": str(song.id),
                        "_score": 1.0,
                        "_source": {
                            "document_id": song.id,
                            "document_type": "Song",
                            "site_id": site.id,
                        },
                    },
                    {
                        "_index": "stories_2023_06_23_06_11_22",
                        "_id": str(story.id),
                        "_score": 1.0,
                        "_source": {
                            "document_id": story.id,
                            "document_type": "Story",
                            "site_id": site.id,
                        },
                    },
                ],
                "total": {"value": 3, "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_es_results

        response = self.client.get(self.get_list_endpoint() + "?hasVideo=true")
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 3
        assert len(response_data["results"]) == 3

    def test_site_slug_param_invalid(self):
        response = self.client.get(self.get_list_endpoint() + "?sites=invalidSlug")
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 0
        assert len(response_data["results"]) == 0

    def test_site_slug_param_partial_invalid(self, mock_search_query_execute):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        song = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)
        story = factories.StoryFactory.create(site=site, visibility=Visibility.PUBLIC)
        image = factories.ImageFactory.create(site=site)

        mock_es_results = {
            "hits": {
                "hits": [
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_id": str(entry.id),
                        "_score": 0.0,
                        "_source": {
                            "document_id": entry.id,
                            "document_type": "DictionaryEntry",
                            "site_id": site.id,
                        },
                    },
                    {
                        "_index": "songs_2023_06_23_06_11_22",
                        "_id": str(song.id),
                        "_score": 0.0,
                        "_source": {
                            "document_id": song.id,
                            "document_type": "Song",
                            "site_id": site.id,
                        },
                    },
                    {
                        "_index": "stories_2023_06_23_06_11_22",
                        "_id": str(story.id),
                        "_score": 0.0,
                        "_source": {
                            "document_id": story.id,
                            "document_type": "Story",
                            "site_id": site.id,
                        },
                    },
                    {
                        "_index": "images_2023_06_23_06_11_22",
                        "_id": str(image.id),
                        "_score": 0.0,
                        "_source": {
                            "document_id": image.id,
                            "document_type": "Image",
                            "site_id": site.id,
                        },
                    },
                ],
                "total": {"value": 4, "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_es_results

        response = self.client.get(
            self.get_list_endpoint() + f"?sites={site.slug},invalidSlug"
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 4
        assert len(response_data["results"]) == 4

    def test_invalid_external_system(self):
        response = self.client.get(
            self.get_list_endpoint() + "?externalSystem=invalidSystem"
        )
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0
