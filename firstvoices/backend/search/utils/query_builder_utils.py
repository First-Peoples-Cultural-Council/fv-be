from elasticsearch_dsl import Q

from backend.search.indices.dictionary_entry_document import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)
from backend.search.utils.constants import VALID_DOCUMENT_TYPES


def get_valid_document_types(input_types):
    allowed_values = VALID_DOCUMENT_TYPES

    if not input_types:
        return allowed_values

    values = input_types.split(",")
    selected_values = [
        value.strip().lower()
        for value in values
        if value.strip().lower() in allowed_values
    ]

    if len(selected_values) == 0:
        return None

    return selected_values


def get_indices(types):
    """
    Returns list of indices to go through depending on the docType
    WORD|PHRASE = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
    SONG = ELASTICSEARCH_SONG_INDEX
    STORY = ELASTICSEARCH_STORY_INDEX
    """
    indices = set()

    for doc_type in types:
        if doc_type == "WORD" or doc_type == "PHRASE":
            indices.add(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX)

    return list(indices)


def get_cleaned_search_term(q):
    """
    clean incoming string.
    case-sensitivity handled by analyzer in the search document.
    """
    return q.strip()


def get_search_term_query(search_term):
    # Exact matching has a higher boost value, then fuzzy matching for both title and translation fields
    fuzzy_match_title_query = Q(
        {
            "fuzzy": {
                "title": {
                    "value": search_term,
                    "fuzziness": "2",  # Documentation recommends "AUTO" for this param
                }
            }
        }
    )
    exact_match_title_query = Q(
        {
            "match_phrase": {
                "title": {
                    "query": search_term,
                    "slop": 3,  # How far apart the terms can be in order to match
                    "boost": 1.3,
                }
            }
        }
    )
    fuzzy_match_translation_query = Q(
        {"fuzzy": {"translation": {"value": search_term, "fuzziness": "2"}}}
    )
    exact_match_translation_query = Q(
        {
            "match_phrase": {
                "translation": {"query": search_term, "slop": 3, "boost": 1.1}
            }
        }
    )
    return Q(
        "bool",
        should=[
            fuzzy_match_title_query,
            exact_match_title_query,
            fuzzy_match_translation_query,
            exact_match_translation_query,
        ],
        minimum_should_match=1,
    )


def get_site_filter_query(site_slug):
    return Q("bool", filter=[Q("term", site_slug=site_slug)])
