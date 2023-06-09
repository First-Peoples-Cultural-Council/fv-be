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
from backend.search.utils.query_builder_utils import get_valid_document_types
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
                        description="retrieves results from all types of documents.",
                    ),
                    OpenApiExample(
                        "words, phrases",
                        value="words, phrases",
                        description="searches for documents in both the words and phrases document types.",
                    ),
                    OpenApiExample(
                        "words",
                        value="words",
                        description="specifically looks for documents in the words document type.",
                    ),
                    OpenApiExample(
                        "words, invalid_type",
                        value="words",
                        description="Ignores invalid document types and returns results only "
                        "for the valid types, such as words",
                    ),
                    OpenApiExample(
                        "invalid_type",
                        value="None",
                        description="if no valid document types are provided, the API returns an empty"
                        " set of results.",
                    ),
                ],
            ),
        ],
    ),
)
class BaseSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""

    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        input_q = self.request.GET.get("q", "")

        input_types_str = self.request.GET.get("types", "")
        valid_types_list = get_valid_document_types(input_types_str)

        search_params = {"q": input_q, "types": valid_types_list, "site_slug": ""}
        return search_params

    def list(self, request, **kwargs):
        search_params = self.get_search_params()

        # If no valid types are passed, return emtpy list as a response
        if not search_params["types"]:
            return Response(data=[])

        # Get search query
        search_query = get_search_query(
            q=search_params["q"],
            site_slug=search_params["site_slug"],
            types=search_params["types"],
        )

        # Get search results
        try:
            response = search_query.execute()
        except ConnectionError:
            raise ElasticSearchConnectionError()

        search_results = response["hits"]["hits"]

        # Adding data to objects
        hydrated_objects = hydrate_objects(search_results, request)

        return Response(data=hydrated_objects)
