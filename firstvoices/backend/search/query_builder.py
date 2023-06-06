from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from backend.search.utils.query_builder_utils import (
    get_cleaned_search_term,
    get_indices,
    get_search_term_query,
    get_site_filter_query,
)


def get_search_object():
    client = Elasticsearch()
    indices = get_indices()
    s = Search(using=client, index=indices)
    return s


def get_search_query(q="", site_slug=""):
    search_query = get_search_object()
    search_term = get_cleaned_search_term(q)

    # Building initial query
    search_query = search_query.query()

    # Building initial query with search term
    if search_term:
        search_query = search_query.query(get_search_term_query(search_term))

    # Add site filter if parameter provided in url
    if site_slug:
        search_query = search_query.query(get_site_filter_query(site_slug))

    return search_query
