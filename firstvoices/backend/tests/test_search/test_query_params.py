import pytest

from backend.search.query_builder import get_search_query
from backend.tests import factories


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
        search_query = get_search_query(q="test_query", domain="both")
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


@pytest.mark.django_db
class TestCategory:
    def setup(self):
        self.site = factories.SiteFactory()
        self.parent_category = factories.ParentCategoryFactory(site=self.site)
        self.child_category = factories.ChildCategoryFactory(
            parent=self.parent_category
        )

    def test_default(self):  # default case
        # relates to: SearchQueryTest.java - CategoryIdTest.testDefault(),
        # CategoryIdTest.test_category_blank_allowed()
        search_query = get_search_query()
        search_query = search_query.to_dict()

        assert "categories" not in str(search_query)

    def test_invalid_category(self):
        # Category is validated at view level before category_id is passed into get_search_query()
        # function which is tested in test_query_builder_utils.py
        pass

    def test_category_without_children(self):
        # relates to: DictionaryObjectTest.java - testCategoryNoChildren()
        search_query = get_search_query(category_id=self.child_category.id)
        search_query = search_query.to_dict()

        filtered_terms = search_query["query"]["bool"]["filter"][0]["terms"]
        assert "categories" in filtered_terms

        assert str(self.child_category.id) in filtered_terms["categories"]
        assert str(self.parent_category.id) not in filtered_terms["categories"]

    def test_category_with_children(self):
        # relates to: DictionaryObjectTest.java - testCategoryWithChildren()
        search_query = get_search_query(category_id=self.parent_category.id)
        search_query = search_query.to_dict()

        filtered_terms = search_query["query"]["bool"]["filter"][0]["terms"]
        assert "categories" in filtered_terms

        assert str(self.child_category.id) in filtered_terms["categories"]
        assert str(self.parent_category.id) in filtered_terms["categories"]


@pytest.mark.django_db
class TestStartsWithChar:
    def setup(self):
        self.site = factories.SiteFactory()

    def test_blank(self):
        # relates to: SearchQueryTest.java - AlphabetCharacterTest.testBoth()
        search_query = get_search_query(starts_with_char="")  # default
        search_query = search_query.to_dict()

        expected_starts_with_query_custom_order = "'prefix': {'custom_order': ''}"
        expected_starts_with_query_title = "'prefix': {'title': ''}"

        assert expected_starts_with_query_custom_order not in str(search_query)
        assert expected_starts_with_query_title not in str(search_query)

    def test_has_custom_order(self):
        # relates to: SearchQueryTest.java - AlphabetCharacterTest.testHasCustomOrder()
        base_char = "oo"
        char_variant = "OO"

        alphabet = factories.AlphabetFactory.create(site=self.site)
        char = factories.CharacterFactory.create(site=self.site, title=base_char)
        factories.CharacterVariantFactory.create(
            site=self.site, title=char_variant, base_character=char
        )
        custom_order = alphabet.get_custom_order(char_variant)

        search_query = get_search_query(
            site_id=self.site.id, starts_with_char=char_variant
        )  # default
        search_query = search_query.to_dict()

        expected_starts_with_query = (
            "'prefix': {'custom_order': '" + custom_order + "'}"
        )

        assert expected_starts_with_query in str(search_query)

    def test_has_no_custom_order(self):
        # relates to: SearchQueryTest.java - AlphabetCharacterTest.testNoCustomOrder()
        factories.AlphabetFactory.create(site=self.site)

        search_query = get_search_query(
            site_id=self.site.id, starts_with_char="red"
        )  # default
        search_query = search_query.to_dict()

        expected_starts_with_query = "'prefix': {'title': 'red'}"
        assert expected_starts_with_query in str(search_query)
