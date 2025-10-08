from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from backend.serializers.export_serializers import DictionaryEntryExportSerializer
from backend.utils.CustomCsvRenderer import CustomCsvRenderer
from backend.views.base_search_entries_views import BASE_SEARCH_PARAMS
from backend.views.search_site_entries_views import (
    SITE_SEARCH_PARAMS,
    SearchSiteEntriesViewSet,
)


@extend_schema_view(
    list=extend_schema(
        description="Export a CSV of dictionary entries.",
        parameters=[
            *SITE_SEARCH_PARAMS,
            *BASE_SEARCH_PARAMS,
            OpenApiParameter(
                name="types",
                description="Filter by type of content. Options are word & phrase.",
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
                        "word",
                        value="word",
                        description="Retrieves all words.",
                    ),
                    OpenApiExample(
                        "phrase",
                        value="phrase",
                        description="Retrieves all phrases.",
                    ),
                ],
            ),
        ],
    )
)
class DictionaryEntryExportViewSet(SearchSiteEntriesViewSet):
    http_method_names = ["get"]
    serializer_classes = {
        "DictionaryEntry": DictionaryEntryExportSerializer,
    }
    renderer_classes = [CustomCsvRenderer, JSONRenderer]
    flatten_fields = {
        "categories": "category",
        "translations": "translation",
        "notes": "note",
        "acknowledgements": "acknowledgement",
        "alternate_spellings": "alternate_spelling",
        "pronunciations": "pronunciation",
        "related_dictionary_entries": "related_entry_id",
    }

    def finalize_response(self, request, response, *args, **kwargs):
        # To return JSON response for errors
        response = super().finalize_response(request, response, *args, **kwargs)

        if getattr(response, "exception", False):
            renderer = JSONRenderer()
            response.accepted_renderer = renderer
            response.accepted_media_type = renderer.media_type
            response.renderer_context = self.get_renderer_context()
            response["Content-Type"] = renderer.media_type
            response.render()
        return response

    # Overriding to return CSV instead of search results
    def list(self, request, **kwargs):
        search_params = self.get_search_params()

        # If anything else is present in the search params except for words or phrases,
        # we pop them out as this API only supports dictionary entries
        filtered_types = [
            entry_type
            for entry_type in search_params["types"]
            if entry_type in ["word", "phrase"]
        ]
        search_params["types"] = filtered_types

        pagination_params = self.get_pagination_params()

        response = self.get_search_response(search_params, pagination_params)
        search_results = response["hits"]["hits"]

        data = self.hydrate(search_results)
        serialized_data = self.serialize_search_results(
            search_results, data, **search_params, **pagination_params
        )
        serialized_data = [
            dictionary_entry["entry"] for dictionary_entry in serialized_data
        ]

        filename = f"dictionary_export_{timezone.localtime(timezone.now()).strftime("%Y_%m_%d_%H_%M_%S")}"
        return Response(
            data=serialized_data,
            headers={"Content-Disposition": f'attachment; filename= "{filename}"'},
        )
