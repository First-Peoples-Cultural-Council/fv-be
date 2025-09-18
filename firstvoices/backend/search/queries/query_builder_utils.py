from enum import Enum

from elasticsearch.dsl import Q

from backend.models import Membership
from backend.models.category import Category
from backend.models.characters import Alphabet
from backend.models.constants import AppRole, Role, Visibility
from backend.permissions.utils import get_app_role
from backend.search.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_MEDIA_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
    TYPE_AUDIO,
    TYPE_DOCUMENT,
    TYPE_IMAGE,
    TYPE_PHRASE,
    TYPE_SONG,
    TYPE_STORY,
    TYPE_VIDEO,
    TYPE_WORD,
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
        elif doc_type in [TYPE_AUDIO, TYPE_DOCUMENT, TYPE_IMAGE, TYPE_VIDEO]:
            indices.add(ELASTICSEARCH_MEDIA_INDEX)

    return list(indices)


def get_cleaned_search_term(q):
    """
    clean and nfc-normalize incoming string.
    case-sensitivity handled by analyzer in the search document.
    """
    return clean_input(q)


# Sub Query Generators


def get_types_query(types):
    # Adding type filters using a negation list
    exclude_list = [
        input_type
        for input_type in [
            TYPE_AUDIO,
            TYPE_DOCUMENT,
            TYPE_IMAGE,
            TYPE_VIDEO,
            TYPE_WORD,
            TYPE_PHRASE,
        ]
        if input_type not in types
    ]

    if exclude_list:
        return Q("bool", filter=[~Q("terms", type=exclude_list)])
    else:
        return None


def get_site_filter_query(site_ids):
    return Q("bool", filter=[Q("terms", site_id=site_ids)])


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


def get_import_job_query(import_job_id):
    return Q("bool", filter=[Q("term", import_job_id=str(import_job_id))])


def get_external_system_query(external_system_id):
    return Q("bool", filter=[Q("term", external_system=str(external_system_id))])


def get_kids_query(kids):
    return Q("bool", filter=[Q("term", exclude_from_kids=not kids)])


def get_games_query(games):
    return Q("bool", filter=[Q("term", exclude_from_games=not games)])


def get_visibility_query(visibility):
    return Q("bool", filter=[Q("terms", visibility=visibility)])


def get_has_audio_query(has_audio):
    return Q("bool", filter=[Q("term", has_audio=has_audio)])


def get_has_document_query(has_document):
    return Q("bool", filter=[Q("term", has_document=has_document)])


def get_has_image_query(has_image):
    return Q("bool", filter=[Q("term", has_image=has_image)])


def get_has_video_query(has_video):
    return Q("bool", filter=[Q("term", has_video=has_video)])


def get_has_translation_query(has_translation):
    return Q("bool", filter=[Q("term", has_translation=has_translation)])


def get_has_unrecognized_chars_query(has_unrecognized_chars):
    return Q("bool", filter=[Q("term", has_unrecognized_chars=has_unrecognized_chars)])


def get_has_categories_query(has_categories):
    return Q("bool", filter=[Q("term", has_categories=has_categories)])


def get_has_related_entries_query(has_related_entries):
    return Q("bool", filter=[Q("term", has_related_entries=has_related_entries)])


def get_has_site_feature_query(site_feature):
    return Q("bool", filter=Q("terms", site_features=site_feature))


def get_min_words_query(min_words):
    return Q("bool", filter=Q("range", title__token_count={"gte": min_words}))


def get_max_words_query(max_words):
    return Q("bool", filter=Q("range", title__token_count={"lte": max_words}))
