from django.contrib.auth.models import AnonymousUser
from elasticsearch_dsl import Search

from backend.search.utils.constants import VALID_DOCUMENT_TYPES
from backend.search.utils.query_builder_utils import (
    get_category_query,
    get_cleaned_search_term,
    get_games_query,
    get_indices,
    get_kids_query,
    get_search_term_query,
    get_site_filter_query,
    get_starts_with_query,
    get_types_query,
    get_view_permissions_filter,
)


def get_search_object(indices):
    s = Search(index=indices)
    return s


def get_search_query(
    user=None,
    q=None,
    site_id=None,
    types=VALID_DOCUMENT_TYPES,
    domain="both",
    starts_with_char="",
    category_id="",
    kids=False,
    games=False,
):
    # Building initial query
    indices = get_indices(types)
    search_object = get_search_object(indices)
    search_query = search_object.query()

    # View permissions
    if user is None:
        user = AnonymousUser()

    permissions_filter = get_view_permissions_filter(user)
    if permissions_filter:
        search_query = search_query.query(permissions_filter)

    # Adding search term and domain filter
    if q:
        cleaned_search_term = get_cleaned_search_term(q)
        if cleaned_search_term:
            search_query = search_query.query(
                get_search_term_query(cleaned_search_term, domain)
            )

    # Add site filter if parameter provided in url
    if site_id:
        search_query = search_query.query(get_site_filter_query(site_id))

    types_query = get_types_query(types)
    if types_query:
        search_query = search_query.query(get_types_query(types))

    if starts_with_char:
        search_query = search_query.query(
            get_starts_with_query(site_id, starts_with_char)
        )

    if category_id:
        search_query = search_query.query(get_category_query(category_id))

    if kids:
        search_query = search_query.query(get_kids_query(kids))

    if games:
        search_query = search_query.query(get_games_query(games))

    return search_query
