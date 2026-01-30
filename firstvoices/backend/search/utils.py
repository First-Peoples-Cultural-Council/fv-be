from elasticsearch.exceptions import ConnectionError

from backend.models import Category, ImportJob, Person
from backend.search.constants import ALL_SEARCH_TYPES, ENTRY_SEARCH_TYPES
from backend.search.validators import (
    get_valid_boolean,
    get_valid_count,
    get_valid_domain,
    get_valid_external_system_id,
    get_valid_instance_id,
    get_valid_search_types,
    get_valid_site_features,
    get_valid_sort,
    get_valid_starts_with_char,
    get_valid_visibility,
)
from backend.utils.character_utils import clean_input
from backend.views.exceptions import ElasticSearchConnectionError


def get_base_search_params(request):
    """
    Returns validated search parameters based on request inputs.
    """
    cleaned_q = clean_input(request.GET.get("q", ""))

    return {
        "q": cleaned_q.lower(),
        "user": request.user,
    }


def get_base_entries_search_params(
    request,
    default_search_types=ENTRY_SEARCH_TYPES,
    allowed_search_types=ALL_SEARCH_TYPES,
):
    """
    Function to return search params in a structured format.
    """
    base_search_params = get_base_search_params(request)

    input_types_str = request.GET.get("types", "")
    valid_types_list = get_valid_search_types(
        input_types_str, default_search_types, allowed_search_types
    )

    input_domain_str = request.GET.get("domain", "")
    valid_domain = get_valid_domain(input_domain_str, "both")

    external_system_input_str = request.GET.get("externalSystem", "")
    external_system_id = get_valid_external_system_id(external_system_input_str)

    kids_flag = request.GET.get("kids", None)
    kids_flag = get_valid_boolean(kids_flag)

    games_flag = request.GET.get("games", None)
    games_flag = get_valid_boolean(games_flag)

    visibility = request.GET.get("visibility", "")
    valid_visibility = get_valid_visibility(visibility, "")

    has_audio = request.GET.get("hasAudio", None)
    has_audio = get_valid_boolean(has_audio)

    has_document = request.GET.get("hasDocument", None)
    has_document = get_valid_boolean(has_document)

    has_image = request.GET.get("hasImage", None)
    has_image = get_valid_boolean(has_image)

    has_video = request.GET.get("hasVideo", None)
    has_video = get_valid_boolean(has_video)

    has_translation = request.GET.get("hasTranslation", None)
    has_translation = get_valid_boolean(has_translation)

    has_unrecognized_chars = request.GET.get("hasUnrecognizedChars", None)
    has_unrecognized_chars = get_valid_boolean(has_unrecognized_chars)

    has_categories = request.GET.get("hasCategories", None)
    has_categories = get_valid_boolean(has_categories)

    has_related_entries = request.GET.get("hasRelatedEntries", None)
    has_related_entries = get_valid_boolean(has_related_entries)

    has_site_feature = request.GET.get("hasSiteFeature", "")
    has_site_feature = get_valid_site_features(has_site_feature)

    min_words = request.GET.get("minWords", None)
    min_words = get_valid_count(min_words, "minWords")

    max_words = request.GET.get("maxWords", None)
    max_words = get_valid_count(max_words, "maxWords")

    sort = request.GET.get("sort", "")
    valid_sort, descending = get_valid_sort(sort)

    return {
        **base_search_params,
        "types": valid_types_list,
        "domain": valid_domain,
        "kids": kids_flag,
        "games": games_flag,
        "visibility": valid_visibility,
        "has_audio": has_audio,
        "has_document": has_document,
        "has_image": has_image,
        "has_video": has_video,
        "has_translation": has_translation,
        "has_unrecognized_chars": has_unrecognized_chars,
        "has_categories": has_categories,
        "has_related_entries": has_related_entries,
        "has_site_feature": has_site_feature,
        "min_words": min_words,
        "max_words": max_words,
        "sort": valid_sort,
        "descending": descending,
        "external_system_id": external_system_id,
    }


def get_site_entries_search_params(
    request,
    site,
    default_search_types=ENTRY_SEARCH_TYPES,
    allowed_search_types=ALL_SEARCH_TYPES,
):
    """
    Add site_slug to search params
    """
    site_id = site.id
    search_params = get_base_entries_search_params(
        request, default_search_types, allowed_search_types
    )
    search_params["sites"] = [str(site_id)]

    starts_with_input_str = request.GET.get("startsWithChar", "")
    starts_with_char = get_valid_starts_with_char(starts_with_input_str)
    if starts_with_char:
        search_params["starts_with_char"] = starts_with_char

    category_input_str = request.GET.get("category", "")
    if category_input_str:
        category_id = get_valid_instance_id(
            site,
            Category,
            category_input_str,
        )
        search_params["category_id"] = category_id
    else:
        search_params["category_id"] = ""

    import_job_input_str = request.GET.get("importJobId", "")
    if import_job_input_str:
        import_job_id = get_valid_instance_id(site, ImportJob, import_job_input_str)
        search_params["import_job_id"] = import_job_id
    else:
        search_params["import_job_id"] = ""

    speaker_ids = request.GET.get("speakers", "")
    if speaker_ids:
        speaker_ids = speaker_ids.split(",")
        for _id in speaker_ids:
            if not get_valid_instance_id(
                site,
                Person,
                _id,
            ):
                speaker_ids.remove(_id)

        if len(speaker_ids) == 0:
            speaker_ids = ""

        search_params["speakers"] = speaker_ids
    else:
        search_params["speakers"] = ""

    return search_params


def has_invalid_base_entries_search_input(search_params):
    return (
        not search_params["types"]
        or not search_params["domain"]
        or search_params["visibility"] is None
        or search_params["external_system_id"] is None
        or (
            search_params["min_words"]
            and search_params["max_words"]
            and search_params["max_words"] < search_params["min_words"]
        )
    )


def has_invalid_site_entries_search_input(search_params):
    return (
        has_invalid_base_entries_search_input(search_params)
        or search_params["category_id"] is None
        or search_params["import_job_id"] is None
        or search_params["speakers"] is None
    )


def has_invalid_all_entries_search_input(search_params):
    return (
        has_invalid_base_entries_search_input(search_params)
        or search_params["sites"] is None
    )


def get_ids_by_type(search_results):
    """Organizes model IDs of the search results by data type.

    Returns: a dictionary where the keys are model names and the values are lists of ids
    """
    data = {}
    for result in search_results:
        model_name = result["_source"]["document_type"]
        model_id = result["_source"]["document_id"]

        if model_name not in data:
            data[model_name] = []

        data[model_name].append(model_id)
    return data


def get_search_response(search_query):
    try:
        response = search_query.execute()
        return response
    except ConnectionError:
        raise ElasticSearchConnectionError()
