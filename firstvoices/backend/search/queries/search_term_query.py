from elasticsearch.dsl import Q

from backend.search.constants import FUZZY_SEARCH_CUTOFF
from backend.search.queries.text_matching import (
    fuzzy_match,
    match_phrase,
    substring_match,
)

BASE_BOOST = 1.0  # default value of boost

# Exact matches (highest)
EXACT_MATCH_PRIMARY_BOOST = 12
EXACT_MATCH_SECONDARY_BOOST = 10
EXACT_MATCH_OTHER_BOOST = 8

# Prefix matches (prioritized higher than contains and fuzzy queries)
PREFIX_MATCH_PRIMARY_BOOST = 9
PREFIX_MATCH_SECONDARY_BOOST = 7
PREFIX_MATCH_OTHER_BOOST = 5

# Substring matches in the middle or suffix (middle and suffix are equal but weaker than prefix matches)
CONTAINS_MATCH_PRIMARY_BOOST = 6
CONTAINS_MATCH_SECONDARY_BOOST = 4
CONTAINS_MATCH_OTHER_BOOST = 3

# Fuzzy matches (lowest)
FUZZY_MATCH_PRIMARY_BOOST = 2
FUZZY_MATCH_SECONDARY_BOOST = 1.5
FUZZY_MATCH_OTHER_BOOST = BASE_BOOST


def get_search_term_query(search_term, domain):
    """
    All model fields are mapped to 6 full text searchable fields, named as:

    primary_language_search_fields
    primary_translation_search_fields
    secondary_language_search_fields
    secondary_translation_search_fields
    other_language_search_fields
    other_translation_search_fields

    Fields are divided based on their importance, and domain (i.e. "language" or "translation").  The "both" domain
    contains a sum of individual fields present in the other 2 domains.

    Each field has a different boost value, such as exact match of primary fields have higher boost than
    exact match of secondary fields or fuzzy match of primary fields.
    Refer to,
    https://firstvoices.atlassian.net/wiki/spaces/FIR/pages/275251209/ElasticSearch#Consistent-search-across-models
    for how fields are mapped in different models and different domains.

    Note: Some models may not map fields to all these categories, i.e. dictionary_entry model has no fields
    in other_language_search_fields
    """

    # Primary fields
    exact_match_primary_language_query = match_phrase(
        q=search_term,
        field="primary_language_search_fields",
        boost=EXACT_MATCH_PRIMARY_BOOST,
    )
    exact_match_primary_translation_query = match_phrase(
        q=search_term,
        field="primary_translation_search_fields",
        boost=EXACT_MATCH_PRIMARY_BOOST,
    )
    prefix_match_primary_language_query = substring_match(
        q=search_term,
        field="primary_language_search_fields",
        boost=PREFIX_MATCH_PRIMARY_BOOST,
        match_type="prefix",
    )
    prefix_match_primary_translation_query = substring_match(
        q=search_term,
        field="primary_translation_search_fields",
        boost=PREFIX_MATCH_PRIMARY_BOOST,
        match_type="prefix",
    )
    contains_match_primary_language_query = substring_match(
        q=search_term,
        field="primary_language_search_fields",
        boost=CONTAINS_MATCH_PRIMARY_BOOST,
    )
    contains_match_primary_translation_query = substring_match(
        q=search_term,
        field="primary_translation_search_fields",
        boost=CONTAINS_MATCH_PRIMARY_BOOST,
    )
    fuzzy_match_primary_language_query = fuzzy_match(
        q=search_term,
        field="primary_language_search_fields",
        boost=FUZZY_MATCH_PRIMARY_BOOST,
    )
    fuzzy_match_primary_translation_query = fuzzy_match(
        q=search_term,
        field="primary_translation_search_fields",
        boost=FUZZY_MATCH_PRIMARY_BOOST,
    )

    # Secondary fields
    exact_match_secondary_language_query = match_phrase(
        q=search_term,
        field="secondary_language_search_fields",
        boost=EXACT_MATCH_SECONDARY_BOOST,
    )
    exact_match_secondary_translation_query = match_phrase(
        q=search_term,
        field="secondary_translation_search_fields",
        boost=EXACT_MATCH_SECONDARY_BOOST,
    )
    prefix_match_secondary_language_query = substring_match(
        q=search_term,
        field="secondary_language_search_fields",
        boost=PREFIX_MATCH_SECONDARY_BOOST,
        match_type="prefix",
    )
    prefix_match_secondary_translation_query = substring_match(
        q=search_term,
        field="secondary_translation_search_fields",
        boost=PREFIX_MATCH_SECONDARY_BOOST,
        match_type="prefix",
    )
    contains_match_secondary_language_query = substring_match(
        q=search_term,
        field="secondary_language_search_fields",
        boost=CONTAINS_MATCH_SECONDARY_BOOST,
    )
    contains_match_secondary_translation_query = substring_match(
        q=search_term,
        field="secondary_translation_search_fields",
        boost=CONTAINS_MATCH_SECONDARY_BOOST,
    )
    fuzzy_match_secondary_language_query = fuzzy_match(
        q=search_term,
        field="secondary_language_search_fields",
        boost=FUZZY_MATCH_SECONDARY_BOOST,
    )
    fuzzy_match_secondary_translation_query = fuzzy_match(
        q=search_term,
        field="secondary_translation_search_fields",
        boost=FUZZY_MATCH_SECONDARY_BOOST,
    )

    # Other fields
    exact_match_other_language_query = match_phrase(
        q=search_term,
        field="other_language_search_fields",
        boost=EXACT_MATCH_OTHER_BOOST,
    )
    exact_match_other_translation_query = match_phrase(
        q=search_term,
        field="other_translation_search_fields",
        boost=EXACT_MATCH_OTHER_BOOST,
    )
    prefix_match_other_language_query = substring_match(
        q=search_term,
        field="other_language_search_fields",
        boost=PREFIX_MATCH_OTHER_BOOST,
        match_type="prefix",
    )
    prefix_match_other_translation_query = substring_match(
        q=search_term,
        field="other_translation_search_fields",
        boost=PREFIX_MATCH_OTHER_BOOST,
        match_type="prefix",
    )
    contains_match_other_language_query = substring_match(
        q=search_term,
        field="other_language_search_fields",
        boost=CONTAINS_MATCH_OTHER_BOOST,
    )
    contains_match_other_translation_query = substring_match(
        q=search_term,
        field="other_translation_search_fields",
        boost=CONTAINS_MATCH_OTHER_BOOST,
    )
    fuzzy_match_other_language_query = fuzzy_match(
        q=search_term,
        field="other_language_search_fields",
        boost=FUZZY_MATCH_OTHER_BOOST,
    )
    fuzzy_match_other_translation_query = fuzzy_match(
        q=search_term,
        field="other_translation_search_fields",
        boost=FUZZY_MATCH_OTHER_BOOST,
    )

    subqueries = []

    subquery_domains = {
        "language": [
            exact_match_primary_language_query,
            exact_match_secondary_language_query,
            exact_match_other_language_query,
            prefix_match_primary_language_query,
            prefix_match_secondary_language_query,
            prefix_match_other_language_query,
            contains_match_primary_language_query,
            contains_match_secondary_language_query,
            contains_match_other_language_query,
        ],
        "translation": [
            exact_match_primary_translation_query,
            exact_match_secondary_translation_query,
            exact_match_other_translation_query,
            prefix_match_primary_translation_query,
            prefix_match_secondary_translation_query,
            prefix_match_other_translation_query,
            contains_match_primary_translation_query,
            contains_match_secondary_translation_query,
            contains_match_other_translation_query,
        ],
        "language_fuzzy": [
            fuzzy_match_primary_language_query,
            fuzzy_match_secondary_language_query,
            fuzzy_match_other_language_query,
        ],
        "translation_fuzzy": [
            fuzzy_match_primary_translation_query,
            fuzzy_match_secondary_translation_query,
            fuzzy_match_other_translation_query,
        ],
    }

    subquery_domains["both"] = (
        subquery_domains["language"] + subquery_domains["translation"]
    )
    subquery_domains["both_fuzzy"] = (
        subquery_domains["language_fuzzy"] + subquery_domains["translation_fuzzy"]
    )

    if len(search_term) >= FUZZY_SEARCH_CUTOFF:
        # Use only exact field matching and no fuzzy matching to avoid excessive computation for large queries
        # and to prevent Elasticsearch from encountering exceptions due to generating too many states
        # during fuzzy search.
        subqueries += subquery_domains.get(domain, [])
    else:
        subqueries += subquery_domains.get(domain, [])
        subqueries += subquery_domains.get(domain + "_fuzzy", [])

    return Q(
        "bool",
        should=subqueries,
        minimum_should_match=1,
    )
