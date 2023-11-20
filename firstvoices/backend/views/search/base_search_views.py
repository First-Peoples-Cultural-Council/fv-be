from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from elasticsearch.exceptions import ConnectionError
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response

from backend.pagination import SearchPageNumberPagination
from backend.search.query_builder import get_search_query
from backend.search.utils.constants import SearchIndexEntryTypes
from backend.search.utils.hydration_utils import hydrate_objects
from backend.search.utils.query_builder_utils import (
    get_valid_boolean,
    get_valid_document_types,
    get_valid_domain,
    get_valid_sort,
    get_valid_visibility,
)
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
            403: OpenApiResponse(description="Todo: Not authorized"),
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
                description="filter by document types. possible options are word, phrase, song",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "",
                        value="",
                        description="Retrieves results from all types of documents.",
                    ),
                    OpenApiExample(
                        "word, phrase, song, story",
                        value="word, phrase, song, story",
                        description="Searches for documents in words, phrases, songs and stories.",
                    ),
                    OpenApiExample(
                        "word",
                        value="word",
                        description="Specifically looks for documents in the Words document type.",
                    ),
                    OpenApiExample(
                        "word, invalid_type",
                        value="word",
                        description="Ignores invalid document types and returns results "
                        "only for the valid types, such as words.",
                    ),
                    OpenApiExample(
                        "invalid_type",
                        value="None",
                        description="If no valid document types are provided, "
                        "the API returns an empty set of results.",
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
                description="Return only kids-friendly entries if true",
                required=False,
                default=False,
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
                        description="No kids filter applied.",
                    ),
                    OpenApiExample(
                        "Apples",
                        value=False,
                        description="Invalid input, defaults to false.",
                    ),
                ],
            ),
            OpenApiParameter(
                name="games",
                description="Return entries which are not excluded from games.",
                required=False,
                default=False,
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
                        description="No games filter applied.",
                    ),
                    OpenApiExample(
                        "Oranges",
                        value=False,
                        description="Invalid input, defaults to false.",
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
                description="Filter by document visibility. Possible options are Team, Members, Public",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "",
                        value="",
                        description="Retrieves results from documents with any visibility.",
                    ),
                    OpenApiExample(
                        "Team",
                        value="Team",
                        description="Searches for documents that are visible to team users on a site.",
                    ),
                    OpenApiExample(
                        "Members",
                        value="Members",
                        description="Searches for documents that are visible to members of a site.",
                    ),
                    OpenApiExample(
                        "Public",
                        value="Public",
                        description="Searches for documents that are visible to the public.",
                    ),
                    OpenApiExample(
                        "Team, Members",
                        value="Team, Members",
                        description="Searches for documents that are visible to team users and members of a site.",
                    ),
                    OpenApiExample(
                        "invalid_type",
                        value="None",
                        description="If no valid document types are provided, "
                        "the API returns an empty set of results.",
                    ),
                ],
            ),
            OpenApiParameter(
                name="sort",
                description="Sort results by date created, date last modified or title. Results can be optionally "
                'returned in descending order by adding "_desc" to the parameter. (eg: "sort=created_desc")',
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "",
                        value="",
                        description="Retrieves results from documents with the default ordering by score.",
                    ),
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
                ],
            ),
        ],
    ),
)
class BaseSearchViewSet(
    ThrottlingMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
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
        valid_types_list = get_valid_document_types(input_types_str)

        input_domain_str = self.request.GET.get("domain", "")
        valid_domain = get_valid_domain(input_domain_str)

        kids_flag = self.request.GET.get("kids", None)
        kids_flag = get_valid_boolean(kids_flag)

        games_flag = self.request.GET.get("games", None)
        games_flag = get_valid_boolean(games_flag)

        visibility = self.request.GET.get("visibility", "")
        valid_visibility = get_valid_visibility(visibility)

        has_audio = self.request.GET.get("hasAudio", False)
        has_audio = get_valid_boolean(has_audio)

        has_video = self.request.GET.get("hasVideo", False)
        has_video = get_valid_boolean(has_video)

        has_image = self.request.GET.get("hasImage", False)
        has_image = get_valid_boolean(has_image)

        sort = self.request.GET.get("sort", "")
        valid_sort, descending = get_valid_sort(sort)

        search_params = {
            "q": input_q,
            "user": user,
            "types": valid_types_list,
            "domain": valid_domain,
            "kids": kids_flag,
            "games": games_flag,
            "site_id": "",  # used in site-search
            "starts_with_char": "",  # used in site-search
            "category_id": "",  # used in site-search
            "visibility": valid_visibility,
            "has_audio": has_audio,
            "has_video": has_video,
            "has_image": has_image,
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

    def list(self, request, **kwargs):
        search_params = self.get_search_params()
        pagination_params = self.get_pagination_params()

        # If no valid types are passed, return emtpy list as a response
        if not search_params["types"]:
            return Response(data=[])

        # If invalid domain is passed, return emtpy list as a response
        if not search_params["domain"]:
            return Response(data=[])

        # If invalid category id, return empty list as a response
        # explicitly checking if its None since it can be empty in case of non site wide search
        if search_params["category_id"] is None:
            return Response(data=[])

        # If invalid visibility is passed, return empty list as a response
        if search_params["visibility"] is None:
            return Response(data=[])

        # Get search query
        search_query = get_search_query(
            user=search_params["user"],
            q=search_params["q"],
            types=search_params["types"],
            domain=search_params["domain"],
            kids=search_params["kids"],
            games=search_params["games"],
            site_id=search_params["site_id"],
            starts_with_char=search_params["starts_with_char"],
            category_id=search_params["category_id"],
            visibility=search_params["visibility"],
            has_audio=search_params["has_audio"],
            has_video=search_params["has_video"],
            has_image=search_params["has_image"],
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
        hydrated_objects = hydrate_objects(search_results)

        page = self.paginator.apply_search_pagination(
            request=request,
            object_list=hydrated_objects,
            count=response["hits"]["total"]["value"],
        )

        if page is not None:
            return self.get_paginated_response(page)

        return Response(data=hydrated_objects)
