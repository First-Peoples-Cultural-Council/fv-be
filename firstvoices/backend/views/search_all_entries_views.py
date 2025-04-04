from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from elasticsearch.exceptions import ConnectionError
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from backend.pagination import SearchPageNumberPagination
from backend.search.query_builder import get_search_query
from backend.search.utils.constants import (
    ENTRY_SEARCH_TYPES,
    LENGTH_FILTER_MAX,
    SearchIndexEntryTypes,
)
from backend.search.utils.hydration_utils import hydrate_objects
from backend.search.utils.validators import (
    get_valid_boolean,
    get_valid_count,
    get_valid_domain,
    get_valid_search_types,
    get_valid_site_features,
    get_valid_site_ids_from_slugs,
    get_valid_sort,
    get_valid_visibility,
)
from backend.views import doc_strings
from backend.views.base_views import ThrottlingMixin
from backend.views.exceptions import ElasticSearchConnectionError


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
        parameters=[
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
                name="category",
                description="Return entries which are associated with the given category or its child categories.",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "",
                        value="",
                        description="Default case. Do not add categories filter.",
                    ),
                    OpenApiExample(
                        "valid UUID",
                        value="valid UUID",
                        description="Return entries which are associated with "
                        "the given category or its child categories.",
                    ),
                    OpenApiExample(
                        "invalid UUID",
                        value="invalid UUID",
                        description="Cannot validate given id, returns empty result set.",
                    ),
                ],
            ),
            OpenApiParameter(
                name="startsWithChar",
                description="Return entries that start with the specified character.",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "",
                        value="",
                        description="Default case. Do not add startsWithChar filter.",
                    ),
                    OpenApiExample(
                        "a",
                        value="a",
                        description="Return all entries starting with a.",
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
            OpenApiParameter(
                name="importJobId",
                description="Filter results based on the associated batch import job.",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "valid UUID",
                        value="6cdb161a-2ce7-4197-813d-1683448128a2",
                        description="Return entries which were imported by the specified job.",
                    ),
                ],
            ),
            OpenApiParameter(
                name="sites",
                description="Filter results based on site. Multiple site slugs can be passed as a comma-separated "
                "list. For searching a single site, see also the site-level search API.",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "One Site",
                        value="site1",
                        description="Return results from site1.",
                    ),
                    OpenApiExample(
                        "Multiple Sites",
                        value="site1,site2",
                        description="Return results from site1 and site2.",
                    ),
                ],
            ),
        ],
    ),
)
class SearchAllEntriesViewSet(ThrottlingMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""
    pagination_class = SearchPageNumberPagination

    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        input_q = self.request.GET.get("q", "")

        user = self.request.user

        input_types_str = self.request.GET.get("types", "")
        valid_types_list = get_valid_search_types(input_types_str, ENTRY_SEARCH_TYPES)

        input_domain_str = self.request.GET.get("domain", "")
        valid_domain = get_valid_domain(input_domain_str, "both")

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

        sites = self.request.GET.get("sites", "")
        valid_site_ids = get_valid_site_ids_from_slugs(sites, user)

        search_params = {
            "q": input_q,
            "user": user,
            "types": valid_types_list,
            "domain": valid_domain,
            "kids": kids_flag,
            "games": games_flag,
            "sites": valid_site_ids,
            "starts_with_char": "",  # used in site-search
            "category_id": "",  # used in site-search
            "import_job_id": "",  # used in site-search
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
        }

        return search_params

    def get_pagination_params(self):
        """
        Function to return pagination params
        """
        default_page_size = self.paginator.get_page_size(self.request)

        page = self.paginator.override_invalid_number(self.request.GET.get("page", 1))

        page_size = self.paginator.override_invalid_number(
            self.request.GET.get("pageSize", default_page_size), default_page_size
        )

        start = (page - 1) * page_size

        pagination_params = {
            "page_size": page_size,
            "page": page,
            "start": start,
        }
        return pagination_params

    def paginate_search_response(self, request, object_list, count):
        page = self.paginator.apply_search_pagination(
            request=request,
            object_list=object_list,
            count=count,
        )

        if page is not None:
            return self.get_paginated_response(page)

        return Response(data=object_list)

    def list(self, request, **kwargs):
        search_params = self.get_search_params()
        pagination_params = self.get_pagination_params()

        if self.has_invalid_input(search_params):
            return self.paginate_search_response(request, [], 0)

        # max cannot be lesser than min num of words
        if (
            search_params["min_words"]
            and search_params["max_words"]
            and search_params["max_words"] < search_params["min_words"]
        ):
            raise serializers.ValidationError(
                {"maxWords": [_("maxWords cannot be lower than minWords.")]}
            )

        # Get search query
        search_query = get_search_query(
            user=search_params["user"],
            q=search_params["q"],
            types=search_params["types"],
            domain=search_params["domain"],
            kids=search_params["kids"],
            games=search_params["games"],
            sites=search_params["sites"],
            starts_with_char=search_params["starts_with_char"],
            category_id=search_params["category_id"],
            import_job_id=search_params["import_job_id"],
            visibility=search_params["visibility"],
            has_audio=search_params["has_audio"],
            has_document=search_params["has_document"],
            has_image=search_params["has_image"],
            has_video=search_params["has_video"],
            has_translation=search_params["has_translation"],
            has_unrecognized_chars=search_params["has_unrecognized_chars"],
            has_related_entries=search_params["has_related_entries"],
            has_categories=search_params["has_categories"],
            has_site_feature=search_params["has_site_feature"],
            min_words=search_params["min_words"],
            max_words=search_params["max_words"],
            random_sort=search_params["sort"] == "random",
        )

        # Pagination
        search_query = search_query.extra(
            from_=pagination_params["start"], size=pagination_params["page_size"]
        )

        sort_direction = "desc" if search_params["descending"] else "asc"
        custom_order_sort = {
            "custom_order": {"unmapped_type": "keyword", "order": sort_direction}
        }
        title_order_sort = {"title.raw": {"order": sort_direction}}

        match search_params["sort"]:
            case "created":
                # Sort by created, then by custom sort order, and finally title. Allows descending order.
                search_query = search_query.sort(
                    {"created": {"order": sort_direction}},
                    custom_order_sort,
                    title_order_sort,
                )
            case "modified":
                # Sort by last_modified, then by custom sort order, and finally title. Allows descending order.
                search_query = search_query.sort(
                    {"last_modified": {"order": sort_direction}},
                    custom_order_sort,
                    title_order_sort,
                )
            case "title":
                # Sort by custom sort order, and finally title. Allows descending order.
                search_query = search_query.sort(
                    custom_order_sort,
                    title_order_sort,
                )
            case _:
                # No order_by param is passed case. Sort by score, then by custom sort order, and finally title.
                search_query = search_query.sort(
                    "_score",
                    custom_order_sort,
                    title_order_sort,
                )

        # Get search results
        try:
            response = search_query.execute()
        except ConnectionError:
            raise ElasticSearchConnectionError()

        search_results = response["hits"]["hits"]

        # Adding data to objects
        hydrated_objects = hydrate_objects(
            search_results, games_flag=search_params["games"]
        )

        return self.paginate_search_response(
            request, hydrated_objects, response["hits"]["total"]["value"]
        )

    def has_invalid_input(self, search_params):
        return (
            not search_params["types"]
            or not search_params["domain"]
            or search_params["category_id"] is None
            or search_params["import_job_id"] is None
            or search_params["visibility"] is None
            or search_params["sites"] is None
        )
