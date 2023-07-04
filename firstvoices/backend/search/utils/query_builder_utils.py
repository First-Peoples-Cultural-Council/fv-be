from enum import Enum

from django.core.exceptions import ValidationError
from elasticsearch_dsl import Q

from backend.models import Membership
from backend.models.category import Category
from backend.models.characters import Alphabet
from backend.models.constants import AppRole, Role, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.permissions.utils import get_app_role
from backend.search.indices.dictionary_entry_document import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)
from backend.search.utils.constants import VALID_DOCUMENT_TYPES

BASE_BOOST = 1.0  # default value of boost
FULL_TEXT_SEARCH_BOOST = 1.1
FUZZY_MATCH_BOOST = 1.2
EXACT_MATCH_BOOST = 1.5


class SearchDomains(Enum):
    BOTH = "both"
    LANGUAGE = "language"
    ENGLISH = "english"


def get_indices(types):
    """
    Returns list of indices to go through depending on the docType
    words|phrases = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
    songs = ELASTICSEARCH_SONG_INDEX
    stories = ELASTICSEARCH_STORY_INDEX
    """
    indices = set()

    for doc_type in types:
        if doc_type == "words" or doc_type == "phrases":
            indices.add(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX)

    return list(indices)


def get_cleaned_search_term(q):
    """
    clean incoming string.
    case-sensitivity handled by analyzer in the search document.
    """
    return q.strip()


# sub-queries utils
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


def get_search_term_query(search_term, domain):
    # Exact matching has a higher boost value, then fuzzy matching for both title and translation fields
    fuzzy_match_title_query = Q(
        {
            "fuzzy": {
                "title": {
                    "value": search_term,
                    "fuzziness": "2",  # Documentation recommends "AUTO" for this param
                    "boost": FUZZY_MATCH_BOOST,
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
                    "boost": EXACT_MATCH_BOOST,
                }
            }
        }
    )
    fuzzy_match_translation_query = Q(
        {
            "fuzzy": {
                "translation": {
                    "value": search_term,
                    "fuzziness": "2",
                    "boost": FUZZY_MATCH_BOOST,
                }
            }
        }
    )
    exact_match_translation_query = Q(
        {
            "match_phrase": {
                "translation": {
                    "query": search_term,
                    "slop": 3,
                    "boost": EXACT_MATCH_BOOST,
                }
            }
        }
    )
    multi_match_query = Q(
        {
            "multi_match": {
                "query": search_term,
                "fields": ["title", "full_text_search_field"],
                "type": "phrase",
                "operator": "OR",
                "boost": FULL_TEXT_SEARCH_BOOST,
            }
        }
    )
    text_search_field_match_query = Q(
        {
            "match_phrase": {
                "full_text_search_field": {"query": search_term, "boost": BASE_BOOST}
            }
        }
    )

    subqueries = []

    subquery_domains = {
        "both": [
            fuzzy_match_title_query,
            exact_match_title_query,
            fuzzy_match_translation_query,
            exact_match_translation_query,
            multi_match_query,
            text_search_field_match_query,
        ],
        "language": [fuzzy_match_title_query, exact_match_title_query],
        "english": [
            fuzzy_match_translation_query,
            exact_match_translation_query,
        ],
    }

    subqueries += subquery_domains.get(domain, [])

    return Q(
        "bool",
        should=subqueries,
        minimum_should_match=1,
    )


def get_site_filter_query(site_id):
    return Q("bool", filter=[Q("term", site_id=site_id)])


def get_view_permissions_filter(user):
    """
    Re-creation of the is_visible_object filter from backend/permissions/filters/view.py
    The logic is translated into an ES query.

    NOTE: If the filter logic or predicates in backend/permissions/filters/view.py change, this function MUST also
    be updated to reflect those changes.
    """

    # base.is_at_least_staff_admin(user)
    # if user has a staff app role or higher, they can see all objects
    app_role = get_app_role(user)
    if app_role >= AppRole.STAFF:
        return None

    # base.has_member_access_to_obj(user) + has_team_access_to_obj(user)
    # create the base bool query
    query = Q("bool")
    filter_list = []

    user_memberships = Membership.objects.filter(user=user)

    for membership in user_memberships:
        # create a filter for each membership
        if (
            membership.role == Role.LANGUAGE_ADMIN
            or membership.role == Role.EDITOR
            or membership.role == Role.ASSISTANT
        ):
            filter_list.append(
                Q("term", site_id=membership.site.id)
                & Q("range", visibility={"gte": Visibility.TEAM})
            )
        elif membership.role == Role.MEMBER:
            filter_list.append(
                Q("term", site_id=membership.site.id)
                & Q("range", visibility={"gte": Visibility.MEMBERS})
            )

    # base.has_public_access_to_obj(user)
    filter_list.append(
        Q("term", site_visibility=Visibility.PUBLIC)
        & Q("term", visibility=Visibility.PUBLIC)
    )

    # add all the filters to the query
    for f in filter_list:
        query.should.append(f)

    return query


def get_starts_with_query(site_id, starts_with_char):
    unknown_character_flag = "⚑"

    # Check if a custom_order_character is present, if present, look up in the custom_order field
    # if not, look in the title field
    alphabet = Alphabet.objects.filter(site_id=site_id).first()
    cleaned_char = alphabet.clean_confusables(starts_with_char)
    custom_order_character = alphabet.get_custom_order(cleaned_char)

    if unknown_character_flag in custom_order_character:
        # unknown custom_order character present, look in title field
        starts_with_filter = Q("prefix", title=starts_with_char)
    else:
        # look in custom_order field
        starts_with_filter = Q("prefix", custom_order=custom_order_character)

    return Q("bool", filter=[starts_with_filter])


def get_category_query(category_id):
    query_categories = []

    # category_id passed down here is validated in the view, assuming the following will always return a category
    category = Category.objects.filter(id=category_id)[0]
    query_categories.append(str(category.id))

    # looking for child categories
    child_categories = category.children.all()
    if len(child_categories):
        for child_category in child_categories:
            query_categories.append(str(child_category.id))

    return Q("bool", filter=[Q("terms", categories=query_categories)])


def get_kids_query(kids):
    return Q("bool", filter=[Q("term", exclude_from_kids=not kids)])


def get_games_query(games):
    return Q("bool", filter=[Q("term", exclude_from_games=not games)])


# Search params validation
def get_valid_document_types(input_types, allowed_values=VALID_DOCUMENT_TYPES):
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


def get_valid_domain(input_domain_str):
    string_lower = input_domain_str.strip().lower()

    if not string_lower:
        return "both"

    if (
        string_lower == SearchDomains.BOTH.value
        or string_lower == SearchDomains.LANGUAGE.value
        or string_lower == SearchDomains.ENGLISH.value
    ):
        return string_lower
    else:  # if invalid string is passed
        return None


def get_valid_starts_with_char(input_str):
    # Starting alphabet can be a combination of characters as well
    # taking only first word if multiple words are supplied
    valid_str = str(input_str).strip().lower().split(" ")[0]
    return valid_str


def get_valid_category_id(site, input_category):
    # If input_category is empty, category filter should not be added
    if input_category:
        try:
            # If category does not belong to the site specified, return empty result set
            valid_category = site.category_set.filter(id=input_category)
            if len(valid_category):
                return valid_category[0].id
        except ValidationError:
            return None

    return None


def get_valid_boolean(input_val):
    # Python treats bool("False") as true, thus manual verification
    if str(input_val).strip().lower() in ["true"]:
        return True
    else:
        return False
