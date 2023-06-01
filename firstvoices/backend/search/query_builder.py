from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search

from backend.search.indices.dictionary_entry_document import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)


def get_search_object():
    client = Elasticsearch()
    indices = get_indices()
    s = Search(using=client, index=indices)
    return s


def get_indices():
    """
    Returns list of indices to go through depending on the docType
    WORD|PHRASE = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
    SONG = ELASTICSEARCH_SONG_INDEX
    STORY = ELASTICSEARCH_STORY_INDEX
    """
    list_of_indices = [ELASTICSEARCH_DICTIONARY_ENTRY_INDEX]
    return list_of_indices


def get_cleaned_search_term(q):
    """
    clean incoming string.
    case-sensitivity handled by analyzer in the search document.
    """
    return q.strip()


def get_search_query(q=""):
    search_query = get_search_object()
    search_term = get_cleaned_search_term(q)

    if search_term:
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
        # todo: Translation fields are to be added to model
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
        search_query = search_query.query(
            Q(
                "bool",
                should=[
                    fuzzy_match_title_query,
                    exact_match_title_query,
                    fuzzy_match_translation_query,
                    exact_match_translation_query,
                ],
                minimum_should_match=1,
            )
        )
    else:
        search_query = search_query.query()

    return search_query
