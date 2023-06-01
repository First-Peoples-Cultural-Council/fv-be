from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from backend.search.indices.dictionary_entry_document import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)


def get_elasticsearch_client():
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


def get_wildcard_search_term(q):
    """
    clean incoming string, and prepare it for a wildcard search.
    """
    q = q.strip().lower()
    if q == "":
        return q
    q = "*" + q + "*"
    return q


def get_search_query(q=""):
    search_query = get_elasticsearch_client()

    search_term = get_wildcard_search_term(q)
    if search_term:
        search_query = search_query.query("wildcard", title=search_term)
    else:
        search_query = search_query.query("wildcard", title="*")

    return search_query
