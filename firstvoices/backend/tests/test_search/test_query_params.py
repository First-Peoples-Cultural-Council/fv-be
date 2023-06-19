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
            "'fuzzy': {'title': {'value': 'test', 'fuzziness': '2', 'boost': 1.2}}"
        )
        expected_exact_match_title_string = (
            "'match_phrase': {'title': {'query': 'test', 'slop': 3, 'boost': 1.5}}"
        )
        expected_fuzzy_match_translation_string = (
            "'fuzzy': {'translation': {'value': 'test', 'fuzziness': '2', "
            "'boost': 1.2}}"
        )
        expected_exact_match_translation_string = (
            "'match_phrase': {'translation': {'query': "
            "'test', 'slop': 3, 'boost': 1.5}}"
        )
        expected_multi_match_string = (
            "'multi_match': {'query': 'test', 'fields': ['title', "
            "'full_text_search_field'], 'type': 'phrase', 'operator': 'OR', 'boost': 1.1}"
        )
        expected_match_full_text_search_string = (
            "'match_phrase': {'full_text_search_field': "
            "{'query': 'test', 'boost': 1.0}}"
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
            "'fuzziness': '2', 'boost': 1.2}}"
        )
        expected_exact_match_string = (
            "'match_phrase': {'title': {'query': "
            "'A Valid Query **With $@&*456Ŧ specials!', 'slop': 3, 'boost': 1.5}}"
        )
        expected_fuzzy_match_translation_string = (
            "'fuzzy': {'translation': {'value': "
            "'A Valid Query **With $@&*456Ŧ specials!', 'fuzziness': '2', 'boost': 1.2}}"
        )
        expected_exact_match_translation_string = (
            "'match_phrase': {'translation': {'query': "
            "'A Valid Query **With $@&*456Ŧ specials!', 'slop': 3, 'boost': 1.5}}"
        )
        expected_multi_match_string = (
            "'multi_match': {'query': 'A Valid Query **With $@&*456Ŧ specials!', 'fields': ['title', "
            "'full_text_search_field'], 'type': 'phrase', 'operator': 'OR', 'boost': 1.1}"
        )
        expected_match_full_text_search_string = (
            "'match_phrase': {'full_text_search_field': {'query': 'A Valid Query **With $@&*456Ŧ specials!', 'boost': "
            "1.0}}"
        )

        assert expected_fuzzy_match_string in str(search_query)
        assert expected_exact_match_string in str(search_query)
        assert expected_fuzzy_match_translation_string in str(search_query)
        assert expected_exact_match_translation_string in str(search_query)
        assert expected_multi_match_string in str(search_query)
        assert expected_match_full_text_search_string in str(search_query)


class TestDomain:
    expected_fuzzy_match_string = (
        "'fuzzy': {'title': {'value': 'test_query', 'fuzziness': '2', 'boost': 1.2}}"
    )
    expected_exact_match_string = (
        "'match_phrase': {'title': {'query': 'test_query', 'slop': 3, 'boost': 1.5}}"
    )
    expected_fuzzy_match_translation_string = (
        "'fuzzy': {'translation': {'value': 'test_query', 'fuzziness': '2',"
        " 'boost': 1.2}}"
    )
    expected_exact_match_translation_string = (
        "'match_phrase': {'translation': {'query': "
        "'test_query', 'slop': 3, 'boost': 1.5}}"
    )
    expected_multi_match_string = (
        "'multi_match': {'query': 'test_query', 'fields': ['title', "
        "'full_text_search_field'], 'type': 'phrase', 'operator': 'OR', 'boost': 1.1}"
    )
    expected_match_full_text_search_string = (
        "'match_phrase': {'full_text_search_field': {'query': 'test_query', 'boost': "
        "1.0}}"
    )

    def test_english(self):
        # relates to: SearchQueryTest.java - testEnglish()
        search_query = get_search_query(q="test_query", domain="english")
        search_query = search_query.to_dict()

        # should contain translation matching
        assert self.expected_exact_match_translation_string in str(search_query)
        assert self.expected_fuzzy_match_translation_string in str(search_query)

        # should not contain title matching
        assert self.expected_exact_match_string not in str(search_query)
        assert self.expected_fuzzy_match_string not in str(search_query)

    def test_language(self):
        # relates to: SearchQueryTest.java - testLanguage()
        search_query = get_search_query(q="test_query", domain="language")
        search_query = search_query.to_dict()

        # should contain title matching
        assert self.expected_exact_match_string in str(search_query)
        assert self.expected_fuzzy_match_string in str(search_query)

        # should not contain translation matching
        assert self.expected_exact_match_translation_string not in str(search_query)
        assert self.expected_fuzzy_match_translation_string not in str(search_query)

    def test_both(self):
        # relates to: SearchQueryTest.java - testBoth()
        search_query = get_search_query(
            q="test_query", domain="both"
        )  # default domain is "both"
        search_query = search_query.to_dict()

        # should contain title matching
        assert self.expected_exact_match_string in str(search_query)
        assert self.expected_fuzzy_match_string in str(search_query)

        # should also contain translation matching
        assert self.expected_exact_match_translation_string in str(search_query)
        assert self.expected_fuzzy_match_translation_string in str(search_query)

        # Should also contain the full text search matches
        assert self.expected_multi_match_string in str(search_query)
        assert self.expected_match_full_text_search_string in str(search_query)
