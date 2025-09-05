from django.utils import timezone
from rest_framework.response import Response

from backend.serializers.export_serializers import DictionaryEntryExportSerializer
from backend.utils.CustomCsvRenderer import CustomCsvRenderer
from backend.views.search_site_entries_views import SearchSiteEntriesViewSet


class DictionaryEntryExportViewSet(SearchSiteEntriesViewSet):
    http_method_names = ["get"]
    serializer_classes = {
        "DictionaryEntry": DictionaryEntryExportSerializer,
    }
    renderer_classes = [CustomCsvRenderer]
    flatten_fields = {
        "categories": "category",
        "translations": "translation",
        "notes": "note",
        "acknowledgements": "acknowledgement",
        "alternate_spellings": "alternate_spelling",
        "pronunciations": "pronunciation",
        "related_video_links": "video_embed_link",
        "related_dictionary_entries": "related_entry_id",
    }

    # Overriding to return CSV instead of search results
    def list(self, request, **kwargs):
        search_params = self.get_search_params()

        # If anything else is present in the search params except for words or phrases,
        # we pop them out as this API only supports dictionary entries
        search_params["types"] = [
            entry_type
            for entry_type in search_params["types"]
            if entry_type in ["word", "phrase"]
        ]

        pagination_params = self.get_pagination_params()

        if self.has_invalid_input(search_params):
            return self.paginate_search_response(request, [], 0)

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
