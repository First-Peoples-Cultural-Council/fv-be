import pytest

from backend.views.search_languages_views import LanguageViewSet


@pytest.mark.django_db
class TestLanguageListQuery:
    def test_retrieves_only_languages(self):
        test_view = LanguageViewSet()
        query = test_view.build_query(None).to_dict()
        assert query["query"] == {
            "bool": {"filter": [{"term": {"document_type": "Language"}}]}
        }

    def test_sorted_alphabetically(self):
        test_view = LanguageViewSet()
        query = test_view.build_query(None).to_dict()
        assert query["sort"] == [{"sort_title": {"order": "asc"}}]


@pytest.mark.django_db
class TestLanguageSearchQuery:
    def test_correct_matching_clauses(self):
        test_view = LanguageViewSet()
        query = test_view.build_query("duck").to_dict()
        subqueries = query["query"]["bool"]["should"]

        assert {"term": {"language_code": {"value": "duck", "boost": 5}}} in subqueries
        assert {
            "term": {"primary_search_fields": {"value": "duck", "boost": 5}}
        } in subqueries
        assert {
            "term": {"secondary_search_fields": {"value": "duck", "boost": 3}}
        } in subqueries
        assert {
            "match": {
                "primary_search_fields": {
                    "query": "duck",
                    "boost": 1.0,
                    "fuzziness": "AUTO",
                }
            }
        } in subqueries
        assert {
            "match": {
                "secondary_search_fields": {
                    "query": "duck",
                    "boost": 1.0,
                    "fuzziness": "AUTO",
                }
            }
        } in subqueries

        assert query["query"]["bool"]["minimum_should_match"] == 1
