import json
from unittest.mock import patch

import pytest
from elasticsearch.dsl import Search

from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentListEndpointMixin,
)
from backend.tests.test_apis.test_search_apis.base_search_test import SearchMocksMixin
from backend.tests.test_apis.test_search_apis.test_search_querying.test_search_entry_results import (
    SearchEntryResultsTestMixin,
)


@pytest.mark.django_db
class TestSiteSearchAPI(
    SearchEntryResultsTestMixin,
    SearchMocksMixin,
    SiteContentListEndpointMixin,
    BaseSiteContentApiTest,
):
    """Remaining tests that cover the site search."""

    API_LIST_VIEW = "api:site-search-list"
    API_DETAIL_VIEW = "api:site-search-detail"

    def get_search_endpoint(self, site=None):
        return f"{self.get_list_endpoint(site_slug=site.slug)}?q=what"

    def test_invalid_category_id(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug) + "?category=xyzCategory"
        )
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    def test_invalid_import_job_id(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug)
            + "?importJobId=invalidImportJob"
        )
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    def test_starts_with_char_param(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        with patch(
            "backend.views.base_search_entries_views.get_base_entries_search_query",
            return_value=Search(),
        ) as mock_get_search_query:
            self.client.get(
                self.get_list_endpoint(site_slug=site.slug) + "?startsWithChar=x"
            )

            assert mock_get_search_query.call_args.kwargs["starts_with_char"] == "x"

    def test_invalid_speaker_ids(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug) + "?speakers=invalidSpeaker"
        )
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0
