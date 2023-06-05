import pytest
from django.http import Http404

from backend.search.query_builder import get_search_query
from backend.tests.factories.access import SiteFactory


@pytest.mark.django_db
class TestSearchFilters:
    def test_invalid_dialect_not_allowed(self):
        with pytest.raises(Http404):
            get_search_query(site_slug="invalid_dialect")

    def test_null_dialect_allowed(self):
        search_query = get_search_query(q="something", site_slug="")
        search_query = search_query.to_dict()

        expected_site_filter = "'filter': [{'term': {'site_slug': ''}}]"
        assert expected_site_filter not in str(search_query)

    def test_valid_dialect(self):
        valid_site = SiteFactory.create()
        search_query = get_search_query(site_slug=valid_site.slug)
        search_query = search_query.to_dict()

        expected_site_filter = (
            "'filter': [{'term': {'site_slug': '" + valid_site.slug + "'}}]"
        )

        assert expected_site_filter in str(search_query)
