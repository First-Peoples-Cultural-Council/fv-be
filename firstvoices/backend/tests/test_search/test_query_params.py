import pytest

from backend.search.query_builder import get_search_query


class TestQueryParams:
    @pytest.mark.parametrize("q", ["", "  "])
    def test_empty_or_spaces_only_search_term(self, q):
        # relates to: SearchQueryTest.java - testBlankReturnsAllResults(), testAllSpacesReturnsAllResults()
        search_query = get_search_query(q=q)
        search_query = search_query.to_dict()

        assert "title" not in str(search_query)

    @pytest.mark.parametrize("q", ["test", " test ", " test", "test "])
    def test_padding_search_term(self, q):
        # relates to: SearchQueryTest.java - testPaddedQuery()
        search_query = get_search_query(q=q)
        search_query = search_query.to_dict()

        expected_fuzzy_match_title_string = (
            "'fuzzy': {'title': {'value': 'test', 'fuzziness': '2'}}"
        )
        expected_exact_match_title_string = (
            "'match_phrase': {'title': {'query': 'test', 'slop': 3, 'boost': 1.1}}"
        )
        expected_fuzzy_match_translation_string = (
            "'fuzzy': {'translation': {'value': 'test', 'fuzziness': '2'}}"
        )
        expected_exact_match_translation_string = (
            "'match_phrase': {'translation': {'query': "
            "'test', 'slop': 3, 'boost': 1.1}}"
        )
        expected_multi_match_string = (
            "'multi_match': {'query': 'test', 'fields': ['title', "
            "'full_text_search_field'], 'type': 'phrase', 'operator': 'OR', 'boost': 1.3}"
        )
        expected_match_full_text_search_string = (
            "'match_phrase': {'full_text_search_field': "
            "{'query': 'test', 'boost': 1.5}}"
        )

        assert expected_fuzzy_match_title_string in str(search_query)
        assert expected_exact_match_title_string in str(search_query)
        assert expected_fuzzy_match_translation_string in str(search_query)
        assert expected_exact_match_translation_string in str(search_query)
        assert expected_multi_match_string in str(search_query)
        assert expected_match_full_text_search_string in str(search_query)

    def test_valid_with_special_chars_query(self):
        # relates to: SearchQueryTest.java - testValidQuery()
        search_query = get_search_query(q="A Valid Query **With $@&*456Ŧ specials!")
        search_query = search_query.to_dict()

        expected_fuzzy_match_string = (
            "'fuzzy': {'title': {'value': 'A Valid Query **With $@&*456Ŧ specials!', "
            "'fuzziness': '2'}}"
        )
        expected_exact_match_string = (
            "'match_phrase': {'title': {'query': "
            "'A Valid Query **With $@&*456Ŧ specials!', 'slop': 3, 'boost': 1.1}}"
        )
        expected_fuzzy_match_translation_string = (
            "'fuzzy': {'translation': {'value': "
            "'A Valid Query **With $@&*456Ŧ specials!', 'fuzziness': '2'}}"
        )
        expected_exact_match_translation_string = (
            "'match_phrase': {'translation': {'query': "
            "'A Valid Query **With $@&*456Ŧ specials!', 'slop': 3, 'boost': 1.1}}"
        )
        expected_multi_match_string = (
            "'multi_match': {'query': 'A Valid Query **With $@&*456Ŧ specials!', 'fields': ['title', "
            "'full_text_search_field'], 'type': 'phrase', 'operator': 'OR', 'boost': 1.3}"
        )
        expected_match_full_text_search_string = (
            "'match_phrase': {'full_text_search_field': {'query': 'A Valid Query **With $@&*456Ŧ specials!', 'boost': "
            "1.5}}"
        )

        assert expected_fuzzy_match_string in str(search_query)
        assert expected_exact_match_string in str(search_query)
        assert expected_fuzzy_match_translation_string in str(search_query)
        assert expected_exact_match_translation_string in str(search_query)
        assert expected_multi_match_string in str(search_query)
        assert expected_match_full_text_search_string in str(search_query)
