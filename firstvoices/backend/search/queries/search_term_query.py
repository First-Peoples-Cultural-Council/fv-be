from elasticsearch.dsl import Q

from backend.search.constants import FUZZY_SEARCH_CUTOFF

BASE_BOOST = 1.0  # default value of boost
EXACT_MATCH_PRIMARY_BOOST = 5
EXACT_MATCH_SECONDARY_BOOST = 4
FUZZY_MATCH_PRIMARY_BOOST = 3
FUZZY_MATCH_SECONDARY_BOOST = 2
EXACT_MATCH_OTHER_BOOST = 1.5
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
    exact_match_primary_language_query = Q(
        {
            "match_phrase": {
                "primary_language_search_fields": {
                    "query": search_term,
                    "slop": 3,  # How far apart the terms can be in order to match
                    "boost": EXACT_MATCH_PRIMARY_BOOST,
                }
            }
        }
    )
    exact_match_primary_translation_query = Q(
        {
            "match_phrase": {
                "primary_translation_search_fields": {
                    "query": search_term,
                    "slop": 3,
                    "boost": EXACT_MATCH_PRIMARY_BOOST,
                }
            }
        }
    )
    fuzzy_match_primary_language_query = Q(
        {
            "fuzzy": {
                "primary_language_search_fields": {
                    "value": search_term,
                    "fuzziness": "2",  # Documentation recommends "AUTO" for this param
                    "boost": FUZZY_MATCH_PRIMARY_BOOST,
                }
            }
        }
    )
    fuzzy_match_primary_translation_query = Q(
        {
            "fuzzy": {
                "primary_translation_search_fields": {
                    "value": search_term,
                    "fuzziness": "2",
                    "boost": FUZZY_MATCH_PRIMARY_BOOST,
                }
            }
        }
    )

    # Secondary fields
    exact_match_secondary_language_query = Q(
        {
            "match_phrase": {
                "secondary_language_search_fields": {
                    "query": search_term,
                    "slop": 3,
                    "boost": EXACT_MATCH_SECONDARY_BOOST,
                }
            }
        }
    )
    exact_match_secondary_translation_query = Q(
        {
            "match_phrase": {
                "secondary_translation_search_fields": {
                    "query": search_term,
                    "slop": 3,
                    "boost": EXACT_MATCH_SECONDARY_BOOST,
                }
            }
        }
    )
    fuzzy_match_secondary_language_query = Q(
        {
            "fuzzy": {
                "secondary_language_search_fields": {
                    "value": search_term,
                    "fuzziness": "2",
                    "boost": FUZZY_MATCH_SECONDARY_BOOST,
                }
            }
        }
    )
    fuzzy_match_secondary_translation_query = Q(
        {
            "fuzzy": {
                "secondary_translation_search_fields": {
                    "value": search_term,
                    "fuzziness": "2",
                    "boost": FUZZY_MATCH_SECONDARY_BOOST,
                }
            }
        }
    )

    # Other fields
    exact_match_other_language_query = Q(
        {
            "match_phrase": {
                "other_language_search_fields": {
                    "query": search_term,
                    "slop": 3,
                    "boost": EXACT_MATCH_OTHER_BOOST,
                }
            }
        }
    )
    exact_match_other_translation_query = Q(
        {
            "match_phrase": {
                "other_translation_search_fields": {
                    "query": search_term,
                    "slop": 3,
                    "boost": EXACT_MATCH_OTHER_BOOST,
                }
            }
        }
    )
    fuzzy_match_other_language_query = Q(
        {
            "fuzzy": {
                "other_language_search_fields": {
                    "value": search_term,
                    "fuzziness": "2",
                    "boost": FUZZY_MATCH_OTHER_BOOST,
                }
            }
        }
    )
    fuzzy_match_other_translation_query = Q(
        {
            "fuzzy": {
                "other_translation_search_fields": {
                    "value": search_term,
                    "fuzziness": "2",
                    "boost": FUZZY_MATCH_OTHER_BOOST,
                }
            }
        }
    )

    subqueries = []

    subquery_domains = {
        "language_exact": [
            exact_match_primary_language_query,
            exact_match_secondary_language_query,
            exact_match_other_language_query,
        ],
        "translation_exact": [
            exact_match_primary_translation_query,
            exact_match_secondary_translation_query,
            exact_match_other_translation_query,
        ],
        "language": [
            exact_match_primary_language_query,
            fuzzy_match_primary_language_query,
            exact_match_secondary_language_query,
            fuzzy_match_secondary_language_query,
            exact_match_other_language_query,
            fuzzy_match_other_language_query,
        ],
        "translation": [
            exact_match_primary_translation_query,
            fuzzy_match_primary_translation_query,
            exact_match_secondary_translation_query,
            fuzzy_match_secondary_translation_query,
            exact_match_other_translation_query,
            fuzzy_match_other_translation_query,
        ],
    }
    subquery_domains["both"] = (
        subquery_domains["language"] + subquery_domains["translation"]
    )
    subquery_domains["both_exact"] = (
        subquery_domains["language_exact"] + subquery_domains["translation_exact"]
    )

    if len(search_term) >= FUZZY_SEARCH_CUTOFF:
        # Use only exact field matching and no fuzzy matching to avoid excessive computation for large queries
        # and to prevent Elasticsearch from encountering exceptions due to generating too many states
        # during fuzzy search.
        subqueries += subquery_domains.get(domain + "_exact", [])
    else:
        subqueries += subquery_domains.get(domain, [])

    return Q(
        "bool",
        should=subqueries,
        minimum_should_match=1,
    )
