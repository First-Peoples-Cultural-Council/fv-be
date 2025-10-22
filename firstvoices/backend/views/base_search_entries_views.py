from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

from backend.search.constants import (
    ENTRY_SEARCH_TYPES,
    LENGTH_FILTER_MAX,
    SearchIndexEntryTypes,
)
from backend.search.queries.query_builder import get_search_query
from backend.search.validators import (
    get_valid_boolean,
    get_valid_count,
    get_valid_domain,
    get_valid_external_system_id,
    get_valid_search_types,
    get_valid_site_features,
    get_valid_sort,
    get_valid_visibility,
)
from backend.serializers.search_result_serializers import (
    AudioSearchResultSerializer,
    DictionaryEntrySearchResultSerializer,
    DocumentSearchResultSerializer,
    ImageSearchResultSerializer,
    SongSearchResultSerializer,
    StorySearchResultSerializer,
    VideoSearchResultSerializer,
)
from backend.views import doc_strings
from backend.views.base_search_views import BaseSearchViewSet

BASE_SEARCH_PARAMS = [
    OpenApiParameter(
        name="q",
        description="search term",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample("ball", value="ball"),
            OpenApiExample("quick brown fox", value="quick brown fox"),
        ],
    ),
    OpenApiParameter(
        name="types",
        description="Filter by type of content. Options are word, phrase, song, story.",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample(
                "",
                value="",
                description="Retrieves all types of results.",
            ),
            OpenApiExample(
                "word, phrase",
                value="word,phrase",
                description="Searches for word and phrase results.",
            ),
            OpenApiExample(
                "song",
                value="song",
                description="Searches for song results only.",
            ),
        ],
    ),
    OpenApiParameter(
        name="domain",
        description="search domain",
        required=False,
        default="both",
        type=str,
        examples=[
            OpenApiExample(
                "",
                value="",
                description="Defaults to both.",
            ),
            OpenApiExample(
                "both",
                value="both",
                description="Searches in both the Language and English domains.",
            ),
            OpenApiExample(
                "translation",
                value="translation",
                description="Performs a search focused on translations.",
            ),
            OpenApiExample(
                "language",
                value="language",
                description="Performs a search focused on titles and language.",
            ),
            OpenApiExample(
                "invalid_domain",
                value="None",
                description="If invalid domain is passed, the API returns an empty set of results.",
            ),
        ],
    ),
    OpenApiParameter(
        name="kids",
        description="Return kids-friendly entries if true, not kids-friendly entries if false, "
        "and all entries if left empty or provided an invalid value.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Return kids-friendly entries only.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Return only entries that are not kid-friendly.",
            ),
            OpenApiExample(
                "Apples",
                value=None,
                description="Invalid input, defaults to all entries.",
            ),
        ],
    ),
    OpenApiParameter(
        name="games",
        description="Return entries which are not excluded from games if true, entries which are excluded from "
        "games if false, and all entries if left empty or provided with an invalid value.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Return entries which are not excluded from games.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Return entries which are excluded from games.",
            ),
            OpenApiExample(
                "Oranges",
                value=False,
                description="Invalid input, defaults to all entries.",
            ),
        ],
    ),
    OpenApiParameter(
        name="visibility",
        description="Filter by visibility. Options are team, members, public",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample(
                "",
                value="",
                description="Returns results with any visibility.",
            ),
            OpenApiExample(
                "Team",
                value="team",
                description="Returns results with team-only visibility.",
            ),
            OpenApiExample(
                "Public, Members",
                value="public,members",
                description="Returns results that have been published with Public or Members-only visibility.",
            ),
        ],
    ),
    OpenApiParameter(
        name="externalSystem",
        description="Filter results based on the associated external system.",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample(
                "ExternalSystemName",
                value="ExternalSystemName",
                description="Return entries which have the specified external system.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasAudio",
        description="Filter results that have related audio.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Returns results that have related audio.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Returns results that do not have related audio.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasDocument",
        description="Filter results that have related documents.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Returns results that have related documents.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Returns results that do not have related documents.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasImage",
        description="Filter results that have related images.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Returns results that have related images.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Returns results that do not have related images.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasVideo",
        description="Filter results that have related videos.",
        required=False,
        default=False,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Returns results that have related videos.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Returns results that do not have related videos.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasTranslation",
        description="Filter results that have a translation or title translation.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Returns results that have a translation or title translation.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Returns results that do not have a translation or title translation.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasUnrecognizedChars",
        description="Filter dictionary entries that contain at least one character in their title that is not "
        "present in the alphabet configuration.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Returns dictionary entries that have unrecognized characters.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Returns dictionary entries that do not have any unrecognized characters.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasCategories",
        description="Filter dictionary entries that have categories.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Returns dictionary entries that have categories.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Returns dictionary entries that do not have categories.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasRelatedEntries",
        description="Filter dictionary entries that have related dictionary entries.",
        required=False,
        default=None,
        type=bool,
        examples=[
            OpenApiExample(
                "True",
                value=True,
                description="Returns dictionary entries that have related dictionary entries.",
            ),
            OpenApiExample(
                "False",
                value=False,
                description="Returns dictionary entries that do not have related dictionary entries.",
            ),
        ],
    ),
    OpenApiParameter(
        name="hasSiteFeature",
        description="Filter results based on site features.",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample(
                "valid site feature key",
                value="EXAMPLE_KEY",
                description="Retrieves results from sites with the EXAMPLE_KEY feature enabled.",
            ),
            OpenApiExample(
                "multiple valid site feature keys",
                value="KEY,another_key",
                description="Retrieves results from sites with KEY, another_key or both features enabled.",
            ),
        ],
    ),
    OpenApiParameter(
        name="minWords",
        description="Filter dictionary entries on the minimum number of words in their title."
        " Only non-negative integer values are allowed."
        " If maxWords is less than minWords, no results will be returned.",
        required=False,
        default="",
        type=int,
        examples=[
            OpenApiExample(
                "2",
                value="2",
                description="Returns dictionary entries with at least 2 words in their title.",
            ),
        ],
    ),
    OpenApiParameter(
        name="maxWords",
        description="Filter dictionary entries on the maximum number of words in their title. "
        "Only non-negative integer values are allowed. "
        f"The maximum value is {LENGTH_FILTER_MAX}. "
        "If maxWords is less than minWords, no results will be returned.",
        required=False,
        default="",
        type=int,
        examples=[
            OpenApiExample(
                "5",
                value="5",
                description="Returns dictionary entries which have at the most 5 words in their title.",
            )
        ],
    ),
    OpenApiParameter(
        name="sort",
        description="Sort results by something other than relevance. Options are: date created, date last "
        "modified, title, or random. Results can be returned in descending order by adding '_desc' to the "
        "parameter. (eg: 'sort=created_desc')",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample(
                "Date Created",
                value="created",
                description="Returns results ordered by the created date and time in ascending order.",
            ),
            OpenApiExample(
                "Date Modified",
                value="modified",
                description="Returns results ordered by the last modified date and time in ascending order.",
            ),
            OpenApiExample(
                "Title",
                value="title",
                description="Returns results ordered by title according to a site's custom alphabet.",
            ),
            OpenApiExample(
                "Date Created Descending",
                value="created_desc",
                description="Returns results ordered by the created date and time in descending order.",
            ),
            OpenApiExample(
                "Date Modified Descending",
                value="modified_desc",
                description="Returns results ordered by the last modified date and time in descending order.",
            ),
            OpenApiExample(
                "Random",
                value="random",
                description="Returns results in random order (e.g., for games).",
            ),
        ],
    ),
]


@extend_schema_view(
    list=extend_schema(
        description="List of search results satisfying the query.",
        responses={
            200: inline_serializer(
                name="SearchResults",
                fields={
                    "searchResultId": serializers.CharField(),
                    "score": serializers.FloatField(),
                    "type": serializers.ChoiceField(
                        choices=SearchIndexEntryTypes.choices
                    ),
                    "entry": serializers.DictField(),
                },
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
        },
        parameters=BASE_SEARCH_PARAMS,
    ),
)
class BaseSearchEntriesViewSet(BaseSearchViewSet):
    """A base viewset for searching language content, including dictionary entries, songs, stories, and media."""

    serializer_classes = {
        "DictionaryEntry": DictionaryEntrySearchResultSerializer,
        "Song": SongSearchResultSerializer,
        "Story": StorySearchResultSerializer,
        "Audio": AudioSearchResultSerializer,
        "Document": DocumentSearchResultSerializer,
        "Image": ImageSearchResultSerializer,
        "Video": VideoSearchResultSerializer,
    }
    valid_types = ENTRY_SEARCH_TYPES

    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        base_search_params = super().get_search_params()

        input_types_str = self.request.GET.get("types", "")
        valid_types_list = get_valid_search_types(input_types_str, self.valid_types)

        input_domain_str = self.request.GET.get("domain", "")
        valid_domain = get_valid_domain(input_domain_str, "both")

        external_system_input_str = self.request.GET.get("externalSystem", "")
        external_system_id = get_valid_external_system_id(external_system_input_str)

        kids_flag = self.request.GET.get("kids", None)
        kids_flag = get_valid_boolean(kids_flag)

        games_flag = self.request.GET.get("games", None)
        games_flag = get_valid_boolean(games_flag)

        visibility = self.request.GET.get("visibility", "")
        valid_visibility = get_valid_visibility(visibility, "")

        has_audio = self.request.GET.get("hasAudio", None)
        has_audio = get_valid_boolean(has_audio)

        has_document = self.request.GET.get("hasDocument", None)
        has_document = get_valid_boolean(has_document)

        has_image = self.request.GET.get("hasImage", None)
        has_image = get_valid_boolean(has_image)

        has_video = self.request.GET.get("hasVideo", None)
        has_video = get_valid_boolean(has_video)

        has_translation = self.request.GET.get("hasTranslation", None)
        has_translation = get_valid_boolean(has_translation)

        has_unrecognized_chars = self.request.GET.get("hasUnrecognizedChars", None)
        has_unrecognized_chars = get_valid_boolean(has_unrecognized_chars)

        has_categories = self.request.GET.get("hasCategories", None)
        has_categories = get_valid_boolean(has_categories)

        has_related_entries = self.request.GET.get("hasRelatedEntries", None)
        has_related_entries = get_valid_boolean(has_related_entries)

        has_site_feature = self.request.GET.get("hasSiteFeature", "")
        has_site_feature = get_valid_site_features(has_site_feature)

        min_words = self.request.GET.get("minWords", None)
        min_words = get_valid_count(min_words, "minWords")

        max_words = self.request.GET.get("maxWords", None)
        max_words = get_valid_count(max_words, "maxWords")

        sort = self.request.GET.get("sort", "")
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

    def build_query(self, **kwargs):
        # Get search query
        search_params = {"random_sort": kwargs.get("sort", "") == "random", **kwargs}

        return get_search_query(**search_params)

    def sort_query(self, search_query, **kwargs):
        sort_direction = "desc" if kwargs.get("descending", False) else "asc"
        custom_order_sort = {
            "custom_order": {"unmapped_type": "keyword", "order": sort_direction}
        }
        title_order_sort = {"title.raw": {"order": sort_direction}}

        match kwargs.get("sort", ""):
            case "created":
                # Sort by created, then by custom sort order, and finally title. Allows descending order.
                return search_query.sort(
                    {"created": {"order": sort_direction}},
                    custom_order_sort,
                    title_order_sort,
                )
            case "modified":
                # Sort by last_modified, then by custom sort order, and finally title. Allows descending order.
                return search_query.sort(
                    {"last_modified": {"order": sort_direction}},
                    custom_order_sort,
                    title_order_sort,
                )
            case "title":
                # Sort by custom sort order, and finally title. Allows descending order.
                return search_query.sort(
                    custom_order_sort,
                    title_order_sort,
                )
            case _:
                # No order_by param is passed case. Sort by score, then by custom sort order, and finally title.
                return search_query.sort(
                    "_score",
                    custom_order_sort,
                    title_order_sort,
                )

    def has_invalid_input(self, search_params):
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        games_flag = self.request.GET.get("games", None)
        games_flag = get_valid_boolean(games_flag)
        context["games_flag"] = games_flag
        return context

    def get_data_to_serialize(self, result, data):
        entry_data = super().get_data_to_serialize(result, data)
        if entry_data is None:
            return None

        return {"search_result_id": result["_id"], "entry": entry_data}

    def make_queryset_eager(self, model_name, queryset):
        """Custom method to pass the user to serializers, to allow for permission-based prefetching.

        Returns: updated queryset
        """
        serializer = self.get_serializer_class(model_name)
        if hasattr(serializer, "make_queryset_eager"):
            return serializer.make_queryset_eager(queryset, self.request.user)
        else:
            return queryset
