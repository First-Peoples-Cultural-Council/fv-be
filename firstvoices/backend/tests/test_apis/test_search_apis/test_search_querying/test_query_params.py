import pytest
from django.contrib.auth.models import AnonymousUser

from backend.models.constants import AppRole, Role, Visibility
from backend.search.constants import FUZZY_SEARCH_CUTOFF
from backend.search.queries.search_term_query import (
    CONTAINS_MATCH_OTHER_BOOST,
    CONTAINS_MATCH_PRIMARY_BOOST,
    CONTAINS_MATCH_SECONDARY_BOOST,
    EXACT_MATCH_OTHER_BOOST,
    EXACT_MATCH_PRIMARY_BOOST,
    EXACT_MATCH_SECONDARY_BOOST,
    FUZZY_MATCH_OTHER_BOOST,
    FUZZY_MATCH_PRIMARY_BOOST,
    FUZZY_MATCH_SECONDARY_BOOST,
    PREFIX_MATCH_OTHER_BOOST,
    PREFIX_MATCH_PRIMARY_BOOST,
    PREFIX_MATCH_SECONDARY_BOOST,
)
from backend.tests import factories
from backend.tests.utils import generate_string
from backend.views.search_all_entries_views import SearchAllEntriesViewSet


def get_match_phrase_query(field_name, query, boost):
    return f"'match_phrase': {{'{field_name}': {{'query': '{query}', 'boost': {boost}, 'slop': 0}}}}"


def get_prefix_query(field_name, query, boost):
    return f"'wildcard': {{'{field_name}': {{'value': '{query}*', 'boost': {boost}}}}}"


def get_contains_query(field_name, query, boost):
    return f"'wildcard': {{'{field_name}': {{'value': '*{query}*', 'boost': {boost}}}}}"


def get_fuzzy_query(field_name, query, boost):
    return f"'match': {{'{field_name}': {{'query': '{query}', 'boost': {boost}, 'fuzziness': 'AUTO'}}}}"


def get_search_query(**kwargs):
    view = SearchAllEntriesViewSet()
    return view.build_query(**kwargs)  # .to_dict()


@pytest.mark.django_db
class TestQueryParams:
    @pytest.mark.parametrize("q", ["", "  "])
    def test_empty_or_spaces_only_search_term(self, q):
        # relates to: SearchQueryTest.java - testBlankReturnsAllResults(), testAllSpacesReturnsAllResults()
        search_query = get_search_query(q=q, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "title" not in str(search_query)

    @pytest.mark.parametrize("q", ["test", " test ", " test", "test "])
    def test_padding_search_term(self, q):
        # relates to: SearchQueryTest.java - testPaddedQuery()
        search_query = get_search_query(q=q, user=AnonymousUser())
        search_query = search_query.to_dict()
        expected_search_term = "test"

        # Primary fields
        expected_exact_match_primary_language_string = get_match_phrase_query(
            "primary_language_search_fields",
            expected_search_term,
            EXACT_MATCH_PRIMARY_BOOST,
        )
        expected_prefix_match_primary_language_string = get_prefix_query(
            "primary_language_search_fields",
            expected_search_term,
            PREFIX_MATCH_PRIMARY_BOOST,
        )
        expected_contains_match_primary_language_string = get_contains_query(
            "primary_language_search_fields",
            expected_search_term,
            CONTAINS_MATCH_PRIMARY_BOOST,
        )
        expected_fuzzy_match_primary_language_string = get_fuzzy_query(
            "primary_language_search_fields",
            expected_search_term,
            FUZZY_MATCH_PRIMARY_BOOST,
        )
        expected_exact_match_primary_translation_string = get_match_phrase_query(
            "primary_translation_search_fields",
            expected_search_term,
            EXACT_MATCH_PRIMARY_BOOST,
        )
        expected_prefix_match_primary_translation_string = get_prefix_query(
            "primary_translation_search_fields",
            expected_search_term,
            PREFIX_MATCH_PRIMARY_BOOST,
        )
        expected_contains_match_primary_translation_string = get_contains_query(
            "primary_translation_search_fields",
            expected_search_term,
            CONTAINS_MATCH_PRIMARY_BOOST,
        )
        expected_fuzzy_match_primary_translation_string = get_fuzzy_query(
            "primary_translation_search_fields",
            expected_search_term,
            FUZZY_MATCH_PRIMARY_BOOST,
        )

        # Secondary fields
        expected_exact_match_secondary_language_string = get_match_phrase_query(
            "secondary_language_search_fields",
            expected_search_term,
            EXACT_MATCH_SECONDARY_BOOST,
        )
        expected_prefix_match_secondary_language_string = get_prefix_query(
            "secondary_language_search_fields",
            expected_search_term,
            PREFIX_MATCH_SECONDARY_BOOST,
        )
        expected_contains_match_secondary_language_string = get_contains_query(
            "secondary_language_search_fields",
            expected_search_term,
            CONTAINS_MATCH_SECONDARY_BOOST,
        )
        expected_fuzzy_match_secondary_language_string = get_fuzzy_query(
            "secondary_language_search_fields",
            expected_search_term,
            FUZZY_MATCH_SECONDARY_BOOST,
        )
        expected_exact_match_secondary_translation_string = get_match_phrase_query(
            "secondary_translation_search_fields",
            expected_search_term,
            EXACT_MATCH_SECONDARY_BOOST,
        )
        expected_prefix_match_secondary_translation_string = get_prefix_query(
            "secondary_translation_search_fields",
            expected_search_term,
            PREFIX_MATCH_SECONDARY_BOOST,
        )
        expected_contains_match_secondary_translation_string = get_contains_query(
            "secondary_translation_search_fields",
            expected_search_term,
            CONTAINS_MATCH_SECONDARY_BOOST,
        )
        expected_fuzzy_match_secondary_translation_string = get_fuzzy_query(
            "secondary_translation_search_fields",
            expected_search_term,
            FUZZY_MATCH_SECONDARY_BOOST,
        )

        # Other fields
        expected_exact_match_other_language_string = get_match_phrase_query(
            "other_language_search_fields",
            expected_search_term,
            EXACT_MATCH_OTHER_BOOST,
        )
        expected_prefix_match_other_language_string = get_prefix_query(
            "other_language_search_fields",
            expected_search_term,
            PREFIX_MATCH_OTHER_BOOST,
        )
        expected_contains_match_other_language_string = get_contains_query(
            "other_language_search_fields",
            expected_search_term,
            CONTAINS_MATCH_OTHER_BOOST,
        )
        expected_fuzzy_match_other_language_string = get_fuzzy_query(
            "other_language_search_fields",
            expected_search_term,
            FUZZY_MATCH_OTHER_BOOST,
        )
        expected_exact_match_other_translation_string = get_match_phrase_query(
            "other_translation_search_fields",
            expected_search_term,
            EXACT_MATCH_OTHER_BOOST,
        )
        expected_prefix_match_other_translation_string = get_prefix_query(
            "other_translation_search_fields",
            expected_search_term,
            PREFIX_MATCH_OTHER_BOOST,
        )
        expected_contains_match_other_translation_string = get_contains_query(
            "other_translation_search_fields",
            expected_search_term,
            CONTAINS_MATCH_OTHER_BOOST,
        )
        expected_fuzzy_match_other_translation_string = get_fuzzy_query(
            "other_translation_search_fields",
            expected_search_term,
            FUZZY_MATCH_OTHER_BOOST,
        )

        assert expected_exact_match_primary_language_string in str(search_query)
        assert expected_prefix_match_primary_language_string in str(search_query)
        assert expected_contains_match_primary_language_string in str(search_query)
        assert expected_fuzzy_match_primary_language_string in str(search_query)
        assert expected_exact_match_primary_translation_string in str(search_query)
        assert expected_prefix_match_primary_translation_string in str(search_query)
        assert expected_contains_match_primary_translation_string in str(search_query)
        assert expected_fuzzy_match_primary_translation_string in str(search_query)

        assert expected_exact_match_secondary_language_string in str(search_query)
        assert expected_prefix_match_secondary_language_string in str(search_query)
        assert expected_contains_match_secondary_language_string in str(search_query)
        assert expected_fuzzy_match_secondary_language_string in str(search_query)
        assert expected_exact_match_secondary_translation_string in str(search_query)
        assert expected_prefix_match_secondary_translation_string in str(search_query)
        assert expected_contains_match_secondary_translation_string in str(search_query)
        assert expected_fuzzy_match_secondary_translation_string in str(search_query)

        assert expected_exact_match_other_language_string in str(search_query)
        assert expected_prefix_match_other_language_string in str(search_query)
        assert expected_contains_match_other_language_string in str(search_query)
        assert expected_fuzzy_match_other_language_string in str(search_query)
        assert expected_exact_match_other_translation_string in str(search_query)
        assert expected_prefix_match_other_translation_string in str(search_query)
        assert expected_contains_match_other_translation_string in str(search_query)
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
        search_query = get_search_query(q=input_str, user=AnonymousUser())
        search_query = search_query.to_dict()

        # Primary fields
        expected_exact_match_primary_language_string = get_match_phrase_query(
            "primary_language_search_fields", expected_str, EXACT_MATCH_PRIMARY_BOOST
        )
        expected_fuzzy_match_primary_language_string = get_fuzzy_query(
            "primary_language_search_fields", expected_str, FUZZY_MATCH_PRIMARY_BOOST
        )
        expected_exact_match_primary_translation_string = get_match_phrase_query(
            "primary_translation_search_fields", expected_str, EXACT_MATCH_PRIMARY_BOOST
        )
        expected_fuzzy_match_primary_translation_string = get_fuzzy_query(
            "primary_translation_search_fields", expected_str, FUZZY_MATCH_PRIMARY_BOOST
        )

        # Secondary fields
        expected_exact_match_secondary_language_string = get_match_phrase_query(
            "secondary_language_search_fields",
            expected_str,
            EXACT_MATCH_SECONDARY_BOOST,
        )
        expected_fuzzy_match_secondary_language_string = get_fuzzy_query(
            "secondary_language_search_fields",
            expected_str,
            FUZZY_MATCH_SECONDARY_BOOST,
        )
        expected_exact_match_secondary_translation_string = get_match_phrase_query(
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
        expected_exact_match_other_language_string = get_match_phrase_query(
            "other_language_search_fields", expected_str, EXACT_MATCH_OTHER_BOOST
        )
        expected_fuzzy_match_other_language_string = get_fuzzy_query(
            "other_language_search_fields", expected_str, FUZZY_MATCH_OTHER_BOOST
        )
        expected_exact_match_other_translation_string = get_match_phrase_query(
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

        search_query = get_search_query(q=search_term, user=AnonymousUser())
        search_query = search_query.to_dict()

        expected_exact_match_primary_language_string = get_match_phrase_query(
            "primary_language_search_fields", search_term, EXACT_MATCH_PRIMARY_BOOST
        )
        expected_fuzzy_match_primary_language_string = get_fuzzy_query(
            "primary_language_search_fields", search_term, FUZZY_MATCH_PRIMARY_BOOST
        )
        expected_exact_match_primary_translation_string = get_match_phrase_query(
            "primary_translation_search_fields", search_term, EXACT_MATCH_PRIMARY_BOOST
        )
        expected_fuzzy_match_primary_translation_string = get_fuzzy_query(
            "primary_translation_search_fields", search_term, FUZZY_MATCH_PRIMARY_BOOST
        )

        # Secondary fields
        expected_exact_match_secondary_language_string = get_match_phrase_query(
            "secondary_language_search_fields", search_term, EXACT_MATCH_SECONDARY_BOOST
        )
        expected_fuzzy_match_secondary_language_string = get_fuzzy_query(
            "secondary_language_search_fields", search_term, FUZZY_MATCH_SECONDARY_BOOST
        )
        expected_exact_match_secondary_translation_string = get_match_phrase_query(
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
        expected_exact_match_other_language_string = get_match_phrase_query(
            "other_language_search_fields", search_term, EXACT_MATCH_OTHER_BOOST
        )
        expected_fuzzy_match_other_language_string = get_fuzzy_query(
            "other_language_search_fields", search_term, FUZZY_MATCH_OTHER_BOOST
        )
        expected_exact_match_other_translation_string = get_match_phrase_query(
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
    search_term = "test_query"

    # Primary language fields
    expected_exact_match_primary_language_string = get_match_phrase_query(
        "primary_language_search_fields",
        search_term,
        EXACT_MATCH_PRIMARY_BOOST,
    )
    expected_fuzzy_match_primary_language_string = get_fuzzy_query(
        "primary_language_search_fields",
        search_term,
        FUZZY_MATCH_PRIMARY_BOOST,
    )
    expected_exact_match_primary_translation_string = get_match_phrase_query(
        "primary_translation_search_fields",
        search_term,
        EXACT_MATCH_PRIMARY_BOOST,
    )
    expected_fuzzy_match_primary_translation_string = get_fuzzy_query(
        "primary_translation_search_fields",
        search_term,
        FUZZY_MATCH_PRIMARY_BOOST,
    )

    # Secondary fields
    expected_exact_match_secondary_language_string = get_match_phrase_query(
        "secondary_language_search_fields",
        search_term,
        EXACT_MATCH_SECONDARY_BOOST,
    )
    expected_fuzzy_match_secondary_language_string = get_fuzzy_query(
        "secondary_language_search_fields",
        search_term,
        FUZZY_MATCH_SECONDARY_BOOST,
    )
    expected_exact_match_secondary_translation_string = get_match_phrase_query(
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
    expected_exact_match_other_language_string = get_match_phrase_query(
        "other_language_search_fields", search_term, EXACT_MATCH_OTHER_BOOST
    )
    expected_fuzzy_match_other_language_string = get_fuzzy_query(
        "other_language_search_fields", search_term, FUZZY_MATCH_OTHER_BOOST
    )
    expected_exact_match_other_translation_string = get_match_phrase_query(
        "other_translation_search_fields", search_term, EXACT_MATCH_OTHER_BOOST
    )
    expected_fuzzy_match_other_translation_string = get_fuzzy_query(
        "other_translation_search_fields", search_term, FUZZY_MATCH_OTHER_BOOST
    )

    def test_english(self):
        # relates to: SearchQueryTest.java - testEnglish()
        search_query = get_search_query(
            q="test_query", domain="translation", user=AnonymousUser()
        )
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
        search_query = get_search_query(
            q="test_query", domain="language", user=AnonymousUser()
        )
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
        search_query = get_search_query(
            q="test_query", domain="both", user=AnonymousUser()
        )
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
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "categories" not in str(search_query)

    def test_category_without_children(self):
        # relates to: DictionaryObjectTest.java - testCategoryNoChildren()
        search_query = get_search_query(
            category_id=self.child_category.id, user=AnonymousUser()
        )
        search_query = search_query.to_dict()
        filters = search_query["query"]["bool"]["filter"]

        category_filter = None
        for f in filters:
            if "terms" in f and "categories" in f["terms"]:
                category_filter = f["terms"]
                break

        assert category_filter is not None

        assert str(self.child_category.id) in category_filter["categories"]
        assert str(self.parent_category.id) not in category_filter["categories"]

    def test_category_with_children(self):
        # relates to: DictionaryObjectTest.java - testCategoryWithChildren()
        search_query = get_search_query(
            category_id=self.parent_category.id, user=AnonymousUser()
        )
        search_query = search_query.to_dict()
        filters = search_query["query"]["bool"]["filter"]

        category_filter = None
        for f in filters:
            if "terms" in f and "categories" in f["terms"]:
                category_filter = f["terms"]
                break

        assert category_filter is not None

        assert str(self.child_category.id) in category_filter["categories"]
        assert str(self.parent_category.id) in category_filter["categories"]


@pytest.mark.django_db
class TestStartsWithChar:
    def setup_method(self):
        self.site = factories.SiteFactory()

    def test_blank(self):
        # relates to: SearchQueryTest.java - AlphabetCharacterTest.testBoth()
        search_query = get_search_query(
            starts_with_char="", user=AnonymousUser()
        )  # default
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
            sites=[self.site.id], starts_with_char=char_variant, user=AnonymousUser()
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
            sites=[self.site.id], starts_with_char="red", user=AnonymousUser()
        )  # default
        search_query = search_query.to_dict()

        expected_starts_with_query = "'prefix': {'title': 'red'}"
        assert expected_starts_with_query in str(search_query)


@pytest.mark.django_db
class TestImportJob:
    def setup_method(self):
        self.site = factories.SiteFactory()
        self.import_job = factories.ImportJobFactory(site=self.site)

    def test_default(self):  # default case
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "import_job" not in str(search_query)

    def test_valid_import_job(self):
        search_query = get_search_query(
            import_job_id=self.import_job.id, user=AnonymousUser()
        )
        search_query = search_query.to_dict()
        filters = search_query["query"]["bool"]["filter"]

        import_job_filter = None
        for f in filters:
            if "term" in f and "import_job_id" in f["term"]:
                import_job_filter = f["term"]
                break

        assert import_job_filter is not None

        assert str(self.import_job.id) in import_job_filter["import_job_id"]


@pytest.mark.django_db
class TestExternalSystem:
    def setup_method(self):
        self.external_system = factories.ExternalDictionaryEntrySystem()

    def test_default(self):  # default case
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "external_system" not in str(search_query)

    def test_valid_import_job(self):
        search_query = get_search_query(
            external_system_id=self.external_system.id, user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        filters = search_query["query"]["bool"]["filter"]

        external_system_filter = None
        for f in filters:
            if "term" in f and "external_system" in f["term"]:
                external_system_filter = f["term"]
                break

        assert external_system_filter is not None
        assert str(self.external_system.id) in external_system_filter["external_system"]


@pytest.mark.django_db
class TestSearchFilters:
    def test_empty_site_id_allowed(self):
        search_query = get_search_query(q="something", sites="", user=AnonymousUser())
        search_query = search_query.to_dict()

        expected_site_filter = "'filter': [{'terms': {'site_id': ['']}}]"
        assert expected_site_filter not in str(search_query)

    def test_valid_dialect(self):
        valid_site = factories.SiteFactory.create()
        search_query = get_search_query(
            sites=[str(valid_site.id)], user=AnonymousUser()
        )
        search_query = search_query.to_dict()
        filters = search_query["query"]["bool"]["filter"]

        site_filter = None
        for f in filters:
            if "terms" in f and "site_id" in f["terms"]:
                site_filter = f["terms"]
                break

        assert site_filter is not None
        assert str(valid_site.id) in site_filter["site_id"]


@pytest.mark.django_db
class TestTypesFilter:
    @pytest.mark.parametrize(
        "type_to_exclude, expected_query",
        [
            (
                ["word"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'image', 'video', 'phrase']}}]}",
            ),
            (
                ["phrase"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'image', 'video', 'word']}}]}",
            ),
            (
                ["audio"],
                "'must_not': [{'terms': {'type': ['document', 'image', 'video', 'word', 'phrase']}}]}",
            ),
            (
                ["document"],
                "'must_not': [{'terms': {'type': ['audio', 'image', 'video', 'word', 'phrase']}}]}",
            ),
            (
                ["image"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'video', 'word', 'phrase']}}]}",
            ),
            (
                ["video"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'image', 'word', 'phrase']}}]}",
            ),
            (
                ["word", "audio"],
                "'must_not': [{'terms': {'type': ['document', 'image', 'video', 'phrase']}}]}",
            ),
            (
                ["word", "phrase"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'image', 'video']}}]}",
            ),
            (
                ["audio", "document", "image", "video"],
                "'must_not': [{'terms': {'type': ['word', 'phrase']}}]}",
            ),
            (
                ["audio", "phrase"],
                "'must_not': [{'terms': {'type': ['document', 'image', 'video', 'word']}}]}",
            ),
        ],
    )
    def test_exclusion_cases(self, type_to_exclude, expected_query):
        search_query = get_search_query(types=type_to_exclude, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_query in str(search_query)

    def test_all_types_supplied(self):
        search_query = get_search_query(
            types=["audio", "document", "image", "video", "word", "phrase"],
            user=AnonymousUser(),
        )
        search_query = search_query.to_dict()

        # Checking there must not be a filter present for types in the query
        assert "'must_not': [{'terms': {'type':" not in str(search_query)


@pytest.mark.django_db
class TestKids:
    # The following boolean flags in the query are opposite of input parameter as
    # the model attribute represent an exclusion criteria
    expected_kids_true_filter = "{'term': {'exclude_from_kids': False}}"
    expected_kids_false_filter = "{'term': {'exclude_from_kids': True}}"

    def test_kids_true(self):
        search_query = get_search_query(kids=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_kids_true_filter in str(search_query)

    def test_kids_false(self):
        search_query = get_search_query(kids=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_kids_false_filter in str(search_query)

    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_kids_true_filter not in str(search_query)
        assert self.expected_kids_false_filter not in str(search_query)


@pytest.mark.django_db
class TestGames:
    # The following boolean flags in the query are opposite of input parameter as
    # the model attribute represent an exclusion criteria
    expected_games_true_filter = "{'term': {'exclude_from_games': False}}"
    expected_games_false_filter = "{'term': {'exclude_from_games': True}}"

    def test_games_true(self):
        search_query = get_search_query(games=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_games_true_filter in str(search_query)

    def test_games_false(self):
        search_query = get_search_query(games=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_games_false_filter in str(search_query)

    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_games_true_filter not in str(search_query)
        assert self.expected_games_false_filter not in str(search_query)


class TestSearchPermissions:
    public_permissions_filter = (
        "'must': [{'term': {'site_visibility': Visibility.PUBLIC}}, {'term': {'visibility': "
        "Visibility.PUBLIC}}]"
    )
    member_permissions_snippet = (
        "{'range': {'visibility': {'gte': Visibility.MEMBERS}}}]"
    )
    team_permissions_snippet = "{'range': {'visibility': {'gte': Visibility.TEAM}}}]"

    @pytest.mark.django_db
    def test_no_user(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.public_permissions_filter in str(search_query)
        assert self.member_permissions_snippet not in str(search_query)
        assert self.team_permissions_snippet not in str(search_query)

    @pytest.mark.django_db
    def test_no_permissions(self):
        user = factories.get_non_member_user()
        search_query = get_search_query(user=user)
        search_query = search_query.to_dict()

        assert self.public_permissions_filter in str(search_query)
        assert self.member_permissions_snippet not in str(search_query)
        assert self.team_permissions_snippet not in str(search_query)

    @pytest.mark.django_db
    def test_member_permissions(self):
        user = factories.get_non_member_user()
        site = factories.SiteFactory.create()
        factories.MembershipFactory.create(user=user, site=site, role=Role.MEMBER)

        member_permissions_filter = (
            "'must': [{'term': {'site_id': UUID('"
            + str(site.id)
            + "')}}, {'range': {'visibility': {'gte': Visibility.MEMBERS}}}]"
        )

        search_query = get_search_query(user=user)
        search_query = search_query.to_dict()

        assert self.public_permissions_filter in str(search_query)
        assert member_permissions_filter in str(search_query)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.LANGUAGE_ADMIN, Role.EDITOR, Role.ASSISTANT])
    def test_team_permissions(self, role):
        user = factories.get_non_member_user()
        site = factories.SiteFactory.create()
        factories.MembershipFactory.create(user=user, site=site, role=role)

        assistant_permissions_filter = (
            "'must': [{'term': {'site_id': UUID('"
            + str(site.id)
            + "')}}, {'range': {'visibility': {'gte': Visibility.TEAM}}}]"
        )

        search_query = get_search_query(user=user)
        search_query = search_query.to_dict()

        assert self.public_permissions_filter in str(search_query)
        assert assistant_permissions_filter in str(search_query)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [AppRole.SUPERADMIN, AppRole.STAFF])
    def test_staff_permissions(self, role):
        user = factories.get_app_admin(role=role)
        factories.SiteFactory.create()

        search_query = get_search_query(user=user)
        search_query = search_query.to_dict()

        assert self.public_permissions_filter not in str(search_query)


class TestVisibilityParam:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()
        default_filters = search_query["query"]["bool"]["filter"]
        visibility_filter = default_filters[0]["bool"]["should"][0]
        default_visibility = visibility_filter["bool"]["must"][1]

        assert default_visibility is not None
        assert default_visibility["term"]["visibility"] == Visibility.PUBLIC

    @pytest.mark.parametrize(
        "visibility",
        [
            [Visibility.PUBLIC],
            [Visibility.MEMBERS],
            [Visibility.TEAM],
            [Visibility.PUBLIC, Visibility.MEMBERS],
            [Visibility.PUBLIC, Visibility.TEAM],
            [Visibility.MEMBERS, Visibility.TEAM],
            [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
        ],
    )
    def test_team(self, visibility):
        search_query = get_search_query(visibility=visibility, user=AnonymousUser())
        search_query = search_query.to_dict()

        filters = search_query["query"]["bool"]["filter"]

        visibility_filter = None
        for f in filters:
            if "terms" in f and "visibility" in f["terms"]:
                visibility_filter = f["terms"]
                break

        assert visibility_filter is not None
        assert len(visibility_filter["visibility"]) == len(visibility)

        for value in visibility:
            assert value in visibility_filter["visibility"]


class TestHasMediaParams:
    HAS_MEDIA = "has_media"
    HAS_MEDIA_LIST = ["has_audio", "has_document", "has_image", "has_video"]

    @pytest.mark.parametrize(HAS_MEDIA, HAS_MEDIA_LIST)
    def test_default(self, has_media):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"]["bool"] or has_media not in str(
            search_query["query"]["bool"]["filter"]
        )

    @pytest.mark.parametrize(HAS_MEDIA, HAS_MEDIA_LIST)
    def test_has_media_true(self, has_media):
        expected_true_filter = f"{{'term': {{'{has_media}': True}}}}"
        search_query = get_search_query(**{has_media: True}, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    @pytest.mark.parametrize(HAS_MEDIA, HAS_MEDIA_LIST)
    def test_has_media_false(self, has_media):
        expected_false_filter = f"{{'term': {{'{has_media}': False}}}}"
        search_query = get_search_query(**{has_media: False}, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    @pytest.mark.parametrize(HAS_MEDIA, HAS_MEDIA_LIST)
    def test_has_media_default(self, has_media):
        expected_true_filter = f"{{'term': {{'{has_media}': True}}}}"
        expected_false_filter = f"{{'term': {{'{has_media}': False}}}}"
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)


class TestHasSiteFeatureParams:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"][
            "bool"
        ] or "site_features" not in str(search_query["query"]["bool"]["filter"])

    @pytest.mark.parametrize(
        "site_features",
        [
            [
                "SHARED_MEDIA",
            ],
            ["TEST_FEATURE_1", "TEST_FEATURE_2"],
            ["SHARED_MEDIA", "TEST_FEATURE_1", "TEST_FEATURE_2"],
        ],
    )
    def test_has_site_features(self, site_features):
        search_query = get_search_query(
            has_site_feature=site_features, user=AnonymousUser()
        )
        search_query = search_query.to_dict()
        filters = search_query["query"]["bool"]["filter"]

        site_features_filter = None
        for f in filters:
            if "terms" in f and "site_features" in f["terms"]:
                site_features_filter = f["terms"]
                break

        assert site_features_filter is not None
        assert len(site_features_filter["site_features"]) == len(site_features)

        for value in site_features:
            assert value in site_features_filter["site_features"]


class TestHasTranslationParams:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"][
            "bool"
        ] or "has_translation" not in str(search_query["query"]["bool"]["filter"])

    def test_has_translation_true(self):
        expected_true_filter = "{'term': {'has_translation': True}}"
        search_query = get_search_query(has_translation=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    def test_has_translation_false(self):
        expected_false_filter = "{'term': {'has_translation': False}}"
        search_query = get_search_query(has_translation=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    def test_has_translation_default(self):
        expected_true_filter = "{'term': {'has_translation': True}}"
        expected_false_filter = "{'term': {'has_translation': False}}"
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)


class TestHasUnrecognizedCharsParam:
    def test_has_unrecognized_chars_true(self):
        expected_true_filter = "{'term': {'has_unrecognized_chars': True}}"
        search_query = get_search_query(
            has_unrecognized_chars=True, user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    def test_has_unrecognized_chars_false(self):
        expected_false_filter = "{'term': {'has_unrecognized_chars': False}}"
        search_query = get_search_query(
            has_unrecognized_chars=False, user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    def test_has_unrecognized_chars_default(self):
        expected_true_filter = "{'term': {'has_unrecognized_chars': True}}"
        expected_false_filter = "{'term': {'has_unrecognized_chars': False}}"

        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)
        assert "filter" not in search_query["query"][
            "bool"
        ] or "has_unrecognized_chars" not in str(
            search_query["query"]["bool"]["filter"]
        )


class TestHasCategoriesParam:
    def test_has_categories_true(self):
        expected_true_filter = "{'term': {'has_categories': True}}"
        search_query = get_search_query(has_categories=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    def test_has_categories_false(self):
        expected_false_filter = "{'term': {'has_categories': False}}"
        search_query = get_search_query(has_categories=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    def test_has_categories_default(self):
        expected_true_filter = "{'term': {'has_categories': True}}"
        expected_false_filter = "{'term': {'has_categories': False}}"

        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)
        assert "filter" not in search_query["query"][
            "bool"
        ] or "has_categories" not in str(search_query["query"]["bool"]["filter"])


class TestHasRelatedEntriesParam:
    def test_has_related_entries_true(self):
        expected_true_filter = "{'term': {'has_related_entries': True}}"
        search_query = get_search_query(has_related_entries=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    def test_has_related_entries_false(self):
        expected_false_filter = "{'term': {'has_related_entries': False}}"
        search_query = get_search_query(has_related_entries=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    def test_has_related_entries_default(self):
        expected_true_filter = "{'term': {'has_related_entries': True}}"
        expected_false_filter = "{'term': {'has_related_entries': False}}"

        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)
        assert "filter" not in search_query["query"][
            "bool"
        ] or "has_related_entries" not in str(search_query["query"]["bool"]["filter"])


class TestRandomSortParams:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert (
            "must" not in search_query["query"]["bool"]
            or "function_score" not in search_query["query"]["bool"]["must"][0]
        )

    def test_random_sort_true(self):
        search_query = get_search_query(random_sort=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "function_score" in search_query["query"]["bool"]["must"][0]
        search_query = search_query["query"]["bool"]["must"][0]["function_score"]
        assert "random_score" in search_query["functions"][0]
        assert "seed" in search_query["functions"][0]["random_score"]
        assert "field" in search_query["functions"][0]["random_score"]
        assert search_query["functions"][0]["random_score"]["field"] == "_seq_no"
        assert 1000 <= search_query["functions"][0]["random_score"]["seed"] <= 9999


class TestWordLengthParams:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert (
            "lte" not in search_query["query"]["bool"]
            and "gte" not in search_query["query"]["bool"]
        )

    def test_min_words(self):
        min_words = 2
        expected_min_words_filter = (
            "{'range': {'title.token_count': {'gte': " + str(min_words) + "}}}"
        )
        search_query = get_search_query(min_words=min_words, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_min_words_filter in str(search_query)

    def test_max_words(self):
        max_words = 5
        expected_max_words_filter = (
            "{'range': {'title.token_count': {'lte': " + str(max_words) + "}}}"
        )
        search_query = get_search_query(max_words=max_words, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_max_words_filter in str(search_query)

    def test_combined_filter(self):
        min_words = 2
        max_words = 5
        expected_min_words_filter = (
            "{'range': {'title.token_count': {'gte': " + str(min_words) + "}}}"
        )
        expected_max_words_filter = (
            "{'range': {'title.token_count': {'lte': " + str(max_words) + "}}}"
        )

        search_query = get_search_query(
            min_words=min_words, max_words=max_words, user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        assert expected_min_words_filter in str(search_query)
        assert expected_max_words_filter in str(search_query)


@pytest.mark.django_db
class TestSpeakersParam:
    def setup_method(self):
        self.site = factories.SiteFactory()
        self.speaker1 = factories.PersonFactory(site=self.site)
        self.speaker2 = factories.PersonFactory(site=self.site)

    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "speakers" not in str(search_query)

    def test_single_speaker(self):
        search_query = get_search_query(
            speakers=[str(self.speaker1.id)], user=AnonymousUser()
        )
        search_query = search_query.to_dict()
        filters = search_query["query"]["bool"]["filter"]

        speakers_filter = None
        for f in filters:
            if "terms" in f and "speakers" in f["terms"]:
                speakers_filter = f["terms"]
                break

        assert speakers_filter is not None
        assert str(self.speaker1.id) in speakers_filter["speakers"]
        assert str(self.speaker2.id) not in speakers_filter["speakers"]

    def test_multiple_speakers(self):
        search_query = get_search_query(
            speakers=[str(self.speaker1.id), str(self.speaker2.id)],
            user=AnonymousUser(),
        )
        search_query = search_query.to_dict()
        filters = search_query["query"]["bool"]["filter"]

        speakers_filter = None
        for f in filters:
            if "terms" in f and "speakers" in f["terms"]:
                speakers_filter = f["terms"]
                break

        assert speakers_filter is not None
        assert str(self.speaker1.id) in speakers_filter["speakers"]
        assert str(self.speaker2.id) in speakers_filter["speakers"]
