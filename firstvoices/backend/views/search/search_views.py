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

from backend.search.query_builder import get_search_query
from backend.search.utils.constants import SearchIndexEntryTypes
from backend.search.utils.object_utils import hydrate_objects
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
class SearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""

    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        input_q = self.request.GET.get("q", "")
        site_slug = self.request.GET.get("site_slug", "")

        return {"q": input_q, "site_slug": site_slug}

    def list(self, request):
        search_params = self.get_search_params()

        # Get search query
        search_query = get_search_query(
            q=search_params["q"], site_slug=search_params["site_slug"]
        )

        # Get search results
        try:
            response = search_query.execute()
        except ConnectionError:
            raise ElasticSearchConnectionError()

        search_results = response["hits"]["hits"]

        # Adding data to objects
        hydrated_objects = hydrate_objects(search_results, request)

        # view permissions and pagination to be applied

        # Structuring response
        return Response(data=hydrated_objects)
