    from elasticsearch_dsl import Search

from backend.search.utils.query_builder_utils import (
    get_cleaned_search_term,
    get_indices,
    get_search_term_query,
    get_site_filter_query,
)


def get_search_object():
    indices = get_indices()
    s = Search(index=indices)
    return s


def get_search_query(q=None, site_slug=None):
    # Building initial query
    search_query = get_search_object()
    search_query = search_query.query()

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

    return search_query
