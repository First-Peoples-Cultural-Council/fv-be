import pytest

from backend.search.query_builder import get_search_query
from backend.tests.factories.access import SiteFactory


@pytest.mark.django_db
class TestSearchFilters:
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


class TestTypesFilter:
    expected_phrases_filter = (
        "{'must_not': [{'match': {'type': TypeOfDictionaryEntry.PHRASE}}]}"
    )
    expected_word_filter = (
        "{'must_not': [{'match': {'type': TypeOfDictionaryEntry.WORD}}]}"
    )

    def test_words(self):
        search_query = get_search_query(types=["words"])
        search_query = search_query.to_dict()

        assert self.expected_phrases_filter in str(search_query)
        assert self.expected_word_filter not in str(search_query)

    def test_phrases(self):
        search_query = get_search_query(types=["phrases"])
        search_query = search_query.to_dict()

        assert self.expected_phrases_filter not in str(search_query)
        assert self.expected_word_filter in str(search_query)

    @pytest.mark.parametrize("types", [["phrases", "words"], ["words", "phrases"]])
    def test_words_and_phrases(self, types):
        search_query = get_search_query(types=types)
        search_query = search_query.to_dict()

        assert self.expected_phrases_filter not in str(search_query)
        assert self.expected_word_filter not in str(search_query)


class TestKids:
    expected_kids_filter = "{'term': {'exclude_from_kids': False}}"

    def test_kids_true(self):
        search_query = get_search_query(kids=True)
        search_query = search_query.to_dict()

        assert self.expected_kids_filter in str(search_query)

    def test_kids_false(self):
        search_query = get_search_query(kids=False)
        search_query = search_query.to_dict()

        assert self.expected_kids_filter not in search_query

    def test_default(self):
        search_query = get_search_query()
        search_query = search_query.to_dict()

        assert self.expected_kids_filter not in search_query


class TestGames:
    expected_games_filter = "{'term': {'exclude_from_games': False}}"

    def test_games_true(self):
        search_query = get_search_query(games=True)
        search_query = search_query.to_dict()

        assert self.expected_games_filter in str(search_query)

    def test_games_false(self):
        search_query = get_search_query(games=False)
        search_query = search_query.to_dict()

        assert self.expected_games_filter not in search_query

    def test_default(self):
        search_query = get_search_query()
        search_query = search_query.to_dict()

        assert self.expected_games_filter not in search_query
