import pytest

from backend.search.query_builder import get_search_query
from backend.search.utils.constants import FUZZY_SEARCH_CUTOFF
from backend.search.utils.search_term_query import (
    EXACT_MATCH_OTHER_BOOST,
    EXACT_MATCH_PRIMARY_BOOST,
    EXACT_MATCH_SECONDARY_BOOST,
    FUZZY_MATCH_OTHER_BOOST,
    FUZZY_MATCH_PRIMARY_BOOST,
    FUZZY_MATCH_SECONDARY_BOOST,
)
from backend.tests import factories
from backend.tests.utils import generate_string


def get_match_query(field_name, query, boost):
    return f"'match_phrase': {{'{field_name}': {{'query': '{query}', 'slop': 3, 'boost': {boost}}}}}"


def get_fuzzy_query(field_name, query, boost):
    return f"'fuzzy': {{'{field_name}': {{'value': '{query}', 'fuzziness': '2', 'boost': {boost}}}}}"


@pytest.mark.django_db
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
        expected_search_term = "test"

        # Primary fields
        expected_exact_match_primary_language_string = get_match_query(
            "primary_language_search_fields",
            expected_search_term,
            EXACT_MATCH_PRIMARY_BOOST,
        )
        expected_fuzzy_match_primary_language_string = get_fuzzy_query(
            "primary_language_search_fields",
            expected_search_term,
            FUZZY_MATCH_PRIMARY_BOOST,
        )
        expected_exact_match_primary_translation_string = get_match_query(
            "primary_translation_search_fields",
            expected_search_term,
            EXACT_MATCH_PRIMARY_BOOST,
        )
        expected_fuzzy_match_primary_translation_string = get_fuzzy_query(
            "primary_translation_search_fields",
            expected_search_term,
            FUZZY_MATCH_PRIMARY_BOOST,
        )

        # Secondary fields
        expected_exact_match_secondary_language_string = get_match_query(
            "secondary_language_search_fields",
            expected_search_term,
            EXACT_MATCH_SECONDARY_BOOST,
        )
        expected_fuzzy_match_secondary_language_string = get_fuzzy_query(
            "secondary_language_search_fields",
            expected_search_term,
            FUZZY_MATCH_SECONDARY_BOOST,
        )
        expected_exact_match_secondary_translation_string = get_match_query(
            "secondary_translation_search_fields",
            expected_search_term,
            EXACT_MATCH_SECONDARY_BOOST,
        )
        expected_fuzzy_match_secondary_translation_string = get_fuzzy_query(
            "secondary_translation_search_fields",
            expected_search_term,
            FUZZY_MATCH_SECONDARY_BOOST,
        )

        # Other fields
        expected_exact_match_other_language_string = get_match_query(
            "other_language_search_fields",
            expected_search_term,
            EXACT_MATCH_OTHER_BOOST,
        )
        expected_fuzzy_match_other_language_string = get_fuzzy_query(
            "other_language_search_fields",
            expected_search_term,
            FUZZY_MATCH_OTHER_BOOST,
        )
        expected_exact_match_other_translation_string = get_match_query(
            "other_translation_search_fields",
            expected_search_term,
            EXACT_MATCH_OTHER_BOOST,
        )
        expected_fuzzy_match_other_translation_string = get_fuzzy_query(
            "other_translation_search_fields",
            expected_search_term,
            FUZZY_MATCH_OTHER_BOOST,
        )

        assert expected_exact_match_primary_language_string in str(search_query)
        assert expected_fuzzy_match_primary_language_string in str(search_query)
        assert expected_exact_match_primary_translation_string in str(search_query)
        assert expected_fuzzy_match_primary_translation_string in str(search_query)

        assert expected_exact_match_secondary_language_string in str(search_query)
        assert expected_fuzzy_match_secondary_language_string in str(search_query)
        assert expected_exact_match_secondary_translation_string in str(search_query)
        assert expected_fuzzy_match_secondary_translation_string in str(search_query)

        assert expected_exact_match_other_language_string in str(search_query)
        assert expected_fuzzy_match_other_language_string in str(search_query)
        assert expected_exact_match_other_translation_string in str(search_query)
        assert expected_fuzzy_match_other_translation_string in str(search_query)

    @pytest.mark.parametrize(
        "input_str, expected_str",
        [
            (
                "A Valid Query **With $@&*456Ŧ specials!",
                "A Valid Query **With $@&*456Ŧ specials!",
            ),
            ("ááááá", "ááááá"),  # nfc normalization
        ],
    )
    def test_valid_with_special_chars_query(self, input_str, expected_str):
        # relates to: SearchQueryTest.java - testValidQuery()
        search_query = get_search_query(q=input_str)
        search_query = search_query.to_dict()

        # Primary fields
        expected_exact_match_primary_language_string = get_match_query(
            "primary_language_search_fields", expected_str, EXACT_MATCH_PRIMARY_BOOST
        )
        expected_fuzzy_match_primary_language_string = get_fuzzy_query(
            "primary_language_search_fields", expected_str, FUZZY_MATCH_PRIMARY_BOOST
        )
        expected_exact_match_primary_translation_string = get_match_query(
            "primary_translation_search_fields", expected_str, EXACT_MATCH_PRIMARY_BOOST
        )
        expected_fuzzy_match_primary_translation_string = get_fuzzy_query(
            "primary_translation_search_fields", expected_str, FUZZY_MATCH_PRIMARY_BOOST
        )

        # Secondary fields
        expected_exact_match_secondary_language_string = get_match_query(
            "secondary_language_search_fields",
            expected_str,
            EXACT_MATCH_SECONDARY_BOOST,
        )
        expected_fuzzy_match_secondary_language_string = get_fuzzy_query(
            "secondary_language_search_fields",
            expected_str,
            FUZZY_MATCH_SECONDARY_BOOST,
        )
        expected_exact_match_secondary_translation_string = get_match_query(
            "secondary_translation_search_fields",
            expected_str,
            EXACT_MATCH_SECONDARY_BOOST,
        )
        expected_fuzzy_match_secondary_translation_string = get_fuzzy_query(
            "secondary_translation_search_fields",
            expected_str,
            FUZZY_MATCH_SECONDARY_BOOST,
        )

        # Other fields
        expected_exact_match_other_language_string = get_match_query(
            "other_language_search_fields", expected_str, EXACT_MATCH_OTHER_BOOST
        )
        expected_fuzzy_match_other_language_string = get_fuzzy_query(
            "other_language_search_fields", expected_str, FUZZY_MATCH_OTHER_BOOST
        )
        expected_exact_match_other_translation_string = get_match_query(
            "other_translation_search_fields", expected_str, EXACT_MATCH_OTHER_BOOST
        )
        expected_fuzzy_match_other_translation_string = get_fuzzy_query(
            "other_translation_search_fields", expected_str, FUZZY_MATCH_OTHER_BOOST
        )

        assert expected_exact_match_primary_language_string in str(search_query)
        assert expected_fuzzy_match_primary_language_string in str(search_query)
        assert expected_exact_match_primary_translation_string in str(search_query)
        assert expected_fuzzy_match_primary_translation_string in str(search_query)

        assert expected_exact_match_secondary_language_string in str(search_query)
        assert expected_fuzzy_match_secondary_language_string in str(search_query)
        assert expected_exact_match_secondary_translation_string in str(search_query)
        assert expected_fuzzy_match_secondary_translation_string in str(search_query)

        assert expected_exact_match_other_language_string in str(search_query)
        assert expected_fuzzy_match_other_language_string in str(search_query)
        assert expected_exact_match_other_translation_string in str(search_query)
        assert expected_fuzzy_match_other_translation_string in str(search_query)

    def test_search_term_length_gt_threshold(self):
        # Testing for search term having length more than the defined fuzzy search cutoff
        search_term = generate_string(FUZZY_SEARCH_CUTOFF + 5)

        search_query = get_search_query(q=search_term)
        search_query = search_query.to_dict()

        expected_exact_match_primary_language_string = get_match_query(
            "primary_language_search_fields", search_term, EXACT_MATCH_PRIMARY_BOOST
        )
        expected_fuzzy_match_primary_language_string = get_fuzzy_query(
            "primary_language_search_fields", search_term, FUZZY_MATCH_PRIMARY_BOOST
        )
        expected_exact_match_primary_translation_string = get_match_query(
            "primary_translation_search_fields", search_term, EXACT_MATCH_PRIMARY_BOOST
        )
        expected_fuzzy_match_primary_translation_string = get_fuzzy_query(
            "primary_translation_search_fields", search_term, FUZZY_MATCH_PRIMARY_BOOST
        )

        # Secondary fields
        expected_exact_match_secondary_language_string = get_match_query(
            "secondary_language_search_fields", search_term, EXACT_MATCH_SECONDARY_BOOST
        )
        expected_fuzzy_match_secondary_language_string = get_fuzzy_query(
            "secondary_language_search_fields", search_term, FUZZY_MATCH_SECONDARY_BOOST
        )
        expected_exact_match_secondary_translation_string = get_match_query(
            "secondary_translation_search_fields",
            search_term,
            EXACT_MATCH_SECONDARY_BOOST,
        )
        expected_fuzzy_match_secondary_translation_string = get_fuzzy_query(
            "secondary_translation_search_fields",
            search_term,
            FUZZY_MATCH_SECONDARY_BOOST,
        )

        # Other fields
        expected_exact_match_other_language_string = get_match_query(
            "other_language_search_fields", search_term, EXACT_MATCH_OTHER_BOOST
        )
        expected_fuzzy_match_other_language_string = get_fuzzy_query(
            "other_language_search_fields", search_term, FUZZY_MATCH_OTHER_BOOST
        )
        expected_exact_match_other_translation_string = get_match_query(
            "other_translation_search_fields", search_term, EXACT_MATCH_OTHER_BOOST
        )
        expected_fuzzy_match_other_translation_string = get_fuzzy_query(
            "other_translation_search_fields", search_term, FUZZY_MATCH_OTHER_BOOST
        )

        assert expected_exact_match_primary_language_string in str(search_query)
        assert expected_fuzzy_match_primary_language_string not in str(search_query)
        assert expected_exact_match_primary_translation_string in str(search_query)
        assert expected_fuzzy_match_primary_translation_string not in str(search_query)

        assert expected_exact_match_secondary_language_string in str(search_query)
        assert expected_fuzzy_match_secondary_language_string not in str(search_query)
        assert expected_exact_match_secondary_translation_string in str(search_query)
        assert expected_fuzzy_match_secondary_translation_string not in str(
            search_query
        )

        assert expected_exact_match_other_language_string in str(search_query)
        assert expected_fuzzy_match_other_language_string not in str(search_query)
        assert expected_exact_match_other_translation_string in str(search_query)
        assert expected_fuzzy_match_other_translation_string not in str(search_query)


@pytest.mark.django_db
class TestDomain:
    # Primary language fields
    expected_exact_match_primary_language_string = (
        "'match_phrase': {'primary_language_search_fields': "
        "{'query': 'test_query', 'slop': 3, 'boost': 5}}"
    )
    expected_fuzzy_match_primary_language_string = (
        "'fuzzy': {'primary_language_search_fields': "
        "{'value': 'test_query', 'fuzziness': '2', 'boost': 3}}"
    )
    expected_exact_match_primary_translation_string = (
        "'match_phrase': {'primary_translation_search_fields': "
        "{'query': 'test_query', 'slop': 3, 'boost': 5}}"
    )
    expected_fuzzy_match_primary_translation_string = (
        "'fuzzy': {'primary_translation_search_fields': "
        "{'value': 'test_query', 'fuzziness': '2', 'boost': 3}}"
    )

    # Secondary fields
    expected_exact_match_secondary_language_string = (
        "'match_phrase': {'secondary_language_search_fields': "
        "{'query': 'test_query', 'slop': 3, 'boost': 4}}"
    )
    expected_fuzzy_match_secondary_language_string = (
        "'fuzzy': {'secondary_language_search_fields': "
        "{'value': 'test_query', 'fuzziness': '2', 'boost': 2}}"
    )
    expected_exact_match_secondary_translation_string = (
        "'match_phrase': {'secondary_translation_search_fields': "
        "{'query': 'test_query', 'slop': 3, 'boost': 4}}"
    )
    expected_fuzzy_match_secondary_translation_string = (
        "'fuzzy': {'secondary_translation_search_fields': "
        "{'value': 'test_query', 'fuzziness': '2', 'boost': 2}}"
    )

    # Other fields
    expected_exact_match_other_language_string = (
        "'match_phrase': {'other_language_search_fields': "
        "{'query': 'test_query', 'slop': 3, 'boost': 1.5}}"
    )
    expected_fuzzy_match_other_language_string = (
        "'fuzzy': {'other_language_search_fields': "
        "{'value': 'test_query', 'fuzziness': '2', 'boost': 1.0}}"
    )
    expected_exact_match_other_translation_string = (
        "'match_phrase': {'other_translation_search_fields': "
        "{'query': 'test_query', 'slop': 3, 'boost': 1.5}}"
    )
    expected_fuzzy_match_other_translation_string = (
        "'fuzzy': {'other_translation_search_fields': "
        "{'value': 'test_query', 'fuzziness': '2', 'boost': 1.0}}"
    )

    def test_english(self):
        # relates to: SearchQueryTest.java - testEnglish()
        search_query = get_search_query(q="test_query", domain="translation")
        search_query = search_query.to_dict()

        # should contain translation matching
        assert self.expected_exact_match_primary_translation_string in str(search_query)
        assert self.expected_fuzzy_match_primary_translation_string in str(search_query)
        assert self.expected_exact_match_secondary_translation_string in str(
            search_query
        )
        assert self.expected_fuzzy_match_secondary_translation_string in str(
            search_query
        )
        assert self.expected_exact_match_other_translation_string in str(search_query)
        assert self.expected_fuzzy_match_other_translation_string in str(search_query)

        # should not contain title matching
        assert self.expected_exact_match_primary_language_string not in str(
            search_query
        )
        assert self.expected_fuzzy_match_primary_language_string not in str(
            search_query
        )
        assert self.expected_exact_match_secondary_language_string not in str(
            search_query
        )
        assert self.expected_fuzzy_match_secondary_language_string not in str(
            search_query
        )
        assert self.expected_exact_match_other_language_string not in str(search_query)
        assert self.expected_fuzzy_match_other_language_string not in str(search_query)

    def test_language(self):
        # relates to: SearchQueryTest.java - testLanguage()
        search_query = get_search_query(q="test_query", domain="language")
        search_query = search_query.to_dict()

        # should contain title matching
        assert self.expected_exact_match_primary_language_string in str(search_query)
        assert self.expected_fuzzy_match_primary_language_string in str(search_query)
        assert self.expected_exact_match_secondary_language_string in str(search_query)
        assert self.expected_fuzzy_match_secondary_language_string in str(search_query)
        assert self.expected_exact_match_other_language_string in str(search_query)
        assert self.expected_fuzzy_match_other_language_string in str(search_query)

        # should not contain translation matching
        assert self.expected_exact_match_primary_translation_string not in str(
            search_query
        )
        assert self.expected_fuzzy_match_primary_translation_string not in str(
            search_query
        )
        assert self.expected_exact_match_secondary_translation_string not in str(
            search_query
        )
        assert self.expected_fuzzy_match_secondary_translation_string not in str(
            search_query
        )
        assert self.expected_exact_match_other_translation_string not in str(
            search_query
        )
        assert self.expected_fuzzy_match_other_translation_string not in str(
            search_query
        )

    def test_both(self):
        # relates to: SearchQueryTest.java - testBoth()
        search_query = get_search_query(q="test_query", domain="both")
        search_query = search_query.to_dict()

        # should contain title matching
        assert self.expected_exact_match_primary_language_string in str(search_query)
        assert self.expected_fuzzy_match_primary_language_string in str(search_query)
        assert self.expected_exact_match_secondary_language_string in str(search_query)
        assert self.expected_fuzzy_match_secondary_language_string in str(search_query)
        assert self.expected_exact_match_other_language_string in str(search_query)
        assert self.expected_fuzzy_match_other_language_string in str(search_query)

        # should also contain translation matching
        assert self.expected_exact_match_primary_translation_string in str(search_query)
        assert self.expected_fuzzy_match_primary_translation_string in str(search_query)
        assert self.expected_exact_match_secondary_translation_string in str(
            search_query
        )
        assert self.expected_fuzzy_match_secondary_translation_string in str(
            search_query
        )
        assert self.expected_exact_match_other_translation_string in str(search_query)
        assert self.expected_fuzzy_match_other_translation_string in str(search_query)


@pytest.mark.django_db
class TestCategory:
    def setup_method(self):
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
    def setup_method(self):
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
