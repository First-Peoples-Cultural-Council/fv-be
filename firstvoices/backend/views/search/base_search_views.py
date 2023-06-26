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
from backend.search.utils.object_utils import hydrate_objects
from backend.search.utils.query_builder_utils import (
    get_valid_boolean,
    get_valid_document_types,
    get_valid_domain,
)
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.exceptions import ElasticSearchConnectionError


@extend_schema_view(
    list=extend_schema(
        description="List of search results satisfying the query.",
        responses={
            200: inline_serializer(
                name="SearchResults",
                fields={
                    "id": serializers.CharField(),
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
            site_slug_parameter,
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
                description="filter by document types",
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
                        "words, phrases",
                        value="words, phrases",
                        description="Searches for documents in both the Words and Phrases document types.",
                    ),
                    OpenApiExample(
                        "words",
                        value="words",
                        description="Specifically looks for documents in the Words document type.",
                    ),
                    OpenApiExample(
                        "words, invalid_type",
                        value="words",
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
                        "english",
                        value="english",
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
        ],
    ),
)
class BaseSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""
    pagination_class = SearchPageNumberPagination

    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        input_q = self.request.GET.get("q", "")

        input_types_str = self.request.GET.get("types", "")
        valid_types_list = get_valid_document_types(input_types_str)

        input_domain_str = self.request.GET.get("domain", "")
        valid_domain = get_valid_domain(input_domain_str)

        kids_flag = self.request.GET.get("kids", False)
        kids_flag = get_valid_boolean(kids_flag)

        games_flag = self.request.GET.get("games", False)
        games_flag = get_valid_boolean(games_flag)

        search_params = {
            "q": input_q,
            "site_id": "",
            "types": valid_types_list,
            "domain": valid_domain,
            "kids": kids_flag,
            "games": games_flag,
        }

        return search_params

    def get_pagination_params(self):
        """
        Function to return pagination params
        """
        default_page_size = self.paginator.get_page_size(self.request)

        page = int(self.request.GET.get("page", 1))
        page_size = int(self.request.GET.get("pageSize", default_page_size))
        start = (page - 1) * page_size
        end = start + page_size

        pagination_params = {
            "page_size": page_size,
            "page": page,
            "start": start,
            "end": end,
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

        # Get search query
        search_query = get_search_query(
            q=search_params["q"],
            site_id=search_params["site_id"],
            types=search_params["types"],
            domain=search_params["domain"],
            kids=search_params["kids"],
            games=search_params["games"],
        )

        # Pagination
        search_query = search_query.extra(
            from_=pagination_params["start"], size=pagination_params["page_size"]
        )

        # Sort by score, then by custom sort order
        search_query = search_query.sort("_score", "custom_order")

        # Get search results
        try:
            response = search_query.execute()
        except ConnectionError:
            raise ElasticSearchConnectionError()

        search_results = response["hits"]["hits"]

        # Adding data to objects
        hydrated_objects = hydrate_objects(search_results, request)

        page = self.paginator.apply_search_pagination(
            request=request,
            object_list=hydrated_objects,
            count=response["hits"]["total"]["value"],
        )

        if page is not None:
            return self.get_paginated_response(page)

        return Response(data=hydrated_objects)
