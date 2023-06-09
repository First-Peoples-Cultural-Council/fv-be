from elasticsearch_dsl import Q, Search

from backend.models.dictionary import TypeOfDictionaryEntry
from backend.search.utils.constants import VALID_DOCUMENT_TYPES
from backend.search.utils.query_builder_utils import (
    get_cleaned_search_term,
    get_indices,
    get_search_term_query,
    get_site_filter_query,
)


def get_search_object(indices):
    s = Search(index=indices)
    return s


def get_types_query(types):
    # Adding type filters
    # If only one of the "words" or "phrases" is present, we need to filter out the other one
    # no action required if both are present
    if "words" in types and "phrases" not in types:
        return Q(~Q("match", type=TypeOfDictionaryEntry.PHRASE))
    elif "phrases" in types and "words" not in types:
        return Q(~Q("match", type=TypeOfDictionaryEntry.WORD))
    else:
        return None


def get_search_query(q=None, site_slug=None, types=VALID_DOCUMENT_TYPES):
    # Building initial query
    indices = get_indices(types)
    search_object = get_search_object(indices)
    search_query = search_object.query()

    # Adding search term
    if q:
        cleaned_search_term = get_cleaned_search_term(q)
        if cleaned_search_term:
            search_query = search_query.query(
                get_search_term_query(cleaned_search_term)
            )

    # Add site filter if parameter provided in url
    if site_slug:
        search_query = search_query.query(get_site_filter_query(site_slug))

    types_query = get_types_query(types)
    if types_query:
        search_query = search_query.query(get_types_query(types))

    return search_query
