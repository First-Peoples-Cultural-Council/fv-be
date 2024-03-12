from enum import Enum

from django.core.exceptions import ValidationError
from elasticsearch_dsl import Q

from backend.models import Membership
from backend.models.category import Category
from backend.models.characters import Alphabet
from backend.models.constants import DEFAULT_TITLE_LENGTH, AppRole, Role, Visibility
from backend.permissions.utils import get_app_role
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_MEDIA_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
    TYPE_AUDIO,
    TYPE_IMAGE,
    TYPE_PHRASE,
    TYPE_SONG,
    TYPE_STORY,
    TYPE_VIDEO,
    TYPE_WORD,
    VALID_DOCUMENT_TYPES,
)
from backend.utils.character_utils import clean_input


class SearchDomains(Enum):
    BOTH = "both"
    LANGUAGE = "language"
    TRANSLATION = "translation"


def get_indices(types):
    """
    Returns list of indices to go through depending on the docType
    words|phrases = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
    songs = ELASTICSEARCH_SONG_INDEX
    stories = ELASTICSEARCH_STORY_INDEX
    """
    indices = set()

    for doc_type in types:
        if doc_type == TYPE_WORD or doc_type == TYPE_PHRASE:
            indices.add(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX)
        elif doc_type == TYPE_SONG:
            indices.add(ELASTICSEARCH_SONG_INDEX)
        elif doc_type == TYPE_STORY:
            indices.add(ELASTICSEARCH_STORY_INDEX)
        elif doc_type == TYPE_AUDIO or doc_type == TYPE_IMAGE or doc_type == TYPE_VIDEO:
            indices.add(ELASTICSEARCH_MEDIA_INDEX)

    return list(indices)


def get_cleaned_search_term(q):
    """
    clean and nfc-normalize incoming string.
    case-sensitivity handled by analyzer in the search document.
    """
    return clean_input(q)


# SUB-QUERY GENERATORS


def get_types_query(types):
    # Adding type filters using a negation list
    exclude_list = [
        input_type
        for input_type in [TYPE_AUDIO, TYPE_IMAGE, TYPE_VIDEO, TYPE_WORD, TYPE_PHRASE]
        if input_type not in types
    ]

    if exclude_list:
        return Q("bool", filter=[~Q("terms", type=exclude_list)])
    else:
        return None


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

    user_memberships = (
        Membership.objects.filter(user=user)
        if user.is_authenticated
        else Membership.objects.none()
    )

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
    alphabet = Alphabet.objects.get_or_create(site_id=site_id)[0]
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


def get_visibility_query(visibility):
    return Q("bool", filter=[Q("terms", visibility=visibility)])


def get_has_audio_query(has_audio):
    return Q("bool", filter=[Q("term", has_audio=has_audio)])


def get_has_video_query(has_video):
    return Q("bool", filter=[Q("term", has_video=has_video)])


def get_has_image_query(has_image):
    return Q("bool", filter=[Q("term", has_image=has_image)])


def get_has_translation_query(has_translation):
    return Q("bool", filter=[Q("term", has_translation=has_translation)])


def get_has_unrecognized_chars_query(has_unrecognized_chars):
    return Q("bool", filter=[Q("term", has_unrecognized_chars=has_unrecognized_chars)])


def get_has_site_feature_query(site_feature):
    return Q("bool", filter=Q("terms", site_features=site_feature))


def get_min_words_query(min_words):
    return Q("bool", filter=Q("range", title__token_count={"gte": min_words}))


def get_max_words_query(max_words):
    return Q("bool", filter=Q("range", title__token_count={"lte": max_words}))


# SEARCH PARAMS VALIDATORS


def get_valid_document_types(input_types, allowed_values=VALID_DOCUMENT_TYPES):
    if not input_types:
        return allowed_values

    values = input_types.split(",")
    selected_values = []

    for value in values:
        stripped_value = value.strip().lower()
        if stripped_value in allowed_values and stripped_value not in selected_values:
            selected_values.append(stripped_value)

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
        or string_lower == SearchDomains.TRANSLATION.value
    ):
        return string_lower
    else:  # if invalid string is passed
        return None


def get_valid_starts_with_char(input_str):
    # Starting alphabet can be a combination of characters as well
    # taking only first word if multiple words are supplied
    valid_str = str(input_str).strip().split(" ")[0]
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
    cleaned_input = str(input_val).strip().lower()

    if cleaned_input == "true":
        return True
    elif cleaned_input == "false":
        return False
    else:
        return None


def get_valid_visibility(input_visibility_str):
    if not input_visibility_str:
        return ""

    input_visibility = input_visibility_str.split(",")
    selected_values = []

    for value in input_visibility:
        string_upper = value.strip().upper()
        if (
            string_upper == Visibility.TEAM.label.upper()
            or string_upper == Visibility.MEMBERS.label.upper()
            or string_upper == Visibility.PUBLIC.label.upper()
        ) and Visibility[string_upper] not in selected_values:
            selected_values.append(Visibility[string_upper])

    if len(selected_values) == 0:
        return None
    return selected_values


def get_valid_sort(input_sort_by_str):
    input_string = input_sort_by_str.lower().strip().split("_")

    descending = len(input_string) > 1 and input_string[1] == "desc"

    if len(input_string) > 0 and (
        input_string[0] == "created"
        or input_string[0] == "modified"
        or input_string[0] == "title"
        or input_string[0] == "random"
    ):
        return input_string[0], descending
    else:  # if invalid string is passed
        return None, None


def get_valid_site_feature(input_site_feature_str):
    if not input_site_feature_str:
        return None

    input_site_feature = input_site_feature_str.split(",")
    selected_values = []

    for value in input_site_feature:
        cleaned_value = value.strip().lower()
        if cleaned_value not in selected_values:
            selected_values.append(cleaned_value)

    if len(selected_values) == 0:
        return None
    return selected_values


def get_valid_count(count, property_name):
    exception_message = "Value must be a non-negative integer."
    max_value = DEFAULT_TITLE_LENGTH

    # If empty, return
    if count is None:
        return count

    try:
        count = int(count)
    except ValueError:
        # If anything is supplied other than a 0, raise Exception
        raise ValidationError({property_name: [exception_message]})

    if count < 0:
        raise ValidationError({property_name: [exception_message]})

    # If a number is supplied greater than the max value, consider max value
    if count > max_value:
        count = max_value

    return count
