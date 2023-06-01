import pytest

from backend.search.query_builder import get_search_query


class TestQueryParams:
    def test_empty_search_term(self):
        search_query = get_search_query(q="")
        search_query = search_query.to_dict()

        expected_wildcard_string = "'wildcard': {'title': '*'}"
        assert expected_wildcard_string in str(search_query)

    @pytest.mark.parametrize("q", ["test", "TEST", "TeSt", " test ", " test", "test "])
    def test_case_and_padding_search_term(self, q):
        search_query = get_search_query(q=q)
        search_query = search_query.to_dict()

        expected_wildcard_string = "'wildcard': {'title': '*test*'}"
        assert expected_wildcard_string in str(search_query)
