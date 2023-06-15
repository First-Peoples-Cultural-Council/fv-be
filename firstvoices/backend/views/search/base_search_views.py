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

from backend import pagination
from backend.search.query_builder import get_search_query
from backend.search.utils.constants import (
    ES_MAX_RESULTS,
    ES_PAGE_SIZE,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import hydrate_objects
from backend.views.exceptions import ElasticSearchConnectionError


class SearchViewPagination(pagination.PageNumberPagination):
    page_size = ES_PAGE_SIZE
    max_page_size = ES_MAX_RESULTS


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
            OpenApiParameter(
                name="q",
                description="search term",
                required=False,
                type=str,
                examples=[
                    OpenApiExample("ball", value="ball"),
                    OpenApiExample("quick brown fox", value="quick brown fox"),
                ],
            )
        ],
    ),
)
class BaseSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""
    pagination_class = SearchViewPagination

    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        input_q = self.request.GET.get("q", "")

        search_params = {"q": input_q, "site_slug": ""}
        return search_params

    def list(self, request, **kwargs):
        search_params = self.get_search_params()

        # Get search query
        search_query = get_search_query(
            q=search_params["q"], site_slug=search_params["site_slug"]
        )

        # Get search results
        try:
            response = search_query[0:ES_MAX_RESULTS].execute()
        except ConnectionError:
            raise ElasticSearchConnectionError()

        search_results = response["hits"]["hits"]

        # Adding data to objects
        hydrated_objects = hydrate_objects(search_results, request)

        page = self.paginate_queryset(hydrated_objects)
        if page is not None:
            return self.get_paginated_response(data=page)

        return Response(data=hydrated_objects)
