from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from search.queries.query_builder import (
    get_base_entries_search_query,
    get_base_entries_sort_query,
    get_base_paginate_query,
)
from search.utils import (
    get_search_response,
    get_site_entries_search_params,
    has_invalid_site_entries_search_input,
)
from search.validators import get_valid_boolean
from views.base_search_views import HydrateSerializeSearchResultsMixin
from views.base_views import SiteContentViewSetMixin

from backend.models.constants import AppRole, Role
from backend.pagination import SearchPageNumberPagination
from backend.permissions.utils import get_app_role, get_site_role
from backend.search.constants import TYPE_PHRASE, TYPE_WORD
from backend.serializers.export_serializers import DictionaryEntryExportSerializer
from backend.utils.CustomCsvRenderer import CustomCsvRenderer
from backend.views.base_search_entries_views import BASE_SEARCH_PARAMS
from backend.views.search_site_entries_views import SITE_SEARCH_PARAMS


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
class DictionaryEntryExportViewSet(
    SiteContentViewSetMixin, HydrateSerializeSearchResultsMixin, viewsets.GenericViewSet
):
    http_method_names = ["get"]
    pagination_class = SearchPageNumberPagination
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
    default_search_types = [TYPE_WORD, TYPE_PHRASE]
    allowed_search_types = [TYPE_WORD, TYPE_PHRASE]

    def initial(self, request, *args, **kwargs):
        """Ensures user has permissions to perform the requested action."""
        super().initial(self.request, *args, **kwargs)

        user = self.request.user
        site = self.get_validated_site()

        # Only language admins, staff or super admins can perform the requested action
        is_at_least_staff = get_app_role(user) >= AppRole.STAFF
        is_language_admin = get_site_role(user, site) == Role.LANGUAGE_ADMIN

        if not (is_at_least_staff or is_language_admin):
            raise PermissionDenied("You do not have permission to perform this action.")

    def get_pagination_params(self):
        # limit page size to 5000 entries for export

        default_page_size = self.paginator.get_page_size(self.request)

        page = self.paginator.override_invalid_number(self.request.GET.get("page", 1))

        page_size = self.paginator.override_invalid_number(
            self.request.GET.get("pageSize", default_page_size), default_page_size
        )

        if page_size > 5000:
            raise ValidationError(
                "pageSize: The maximum number of entries per export is 5000."
            )

        start = (page - 1) * page_size

        return {
            "page_size": page_size,
            "page": page,
            "start": start,
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
        serializer = self.get_serializer_class_for_model_type(model_name)
        if hasattr(serializer, "make_queryset_eager"):
            return serializer.make_queryset_eager(queryset, self.request.user)
        else:
            return queryset

    # Overriding to return CSV instead of search results
    def list(self, request, **kwargs):
        site = self.get_validated_site()
        filename = f"dictionary_export_{site.slug}_{timezone.localtime(timezone.now()).strftime("%Y_%m_%d_%H_%M_%S")}"

        search_params = get_site_entries_search_params(
            request, site, self.default_search_types, self.allowed_search_types
        )
        if has_invalid_site_entries_search_input(search_params):
            return Response(
                data=[],
                headers={"Content-Disposition": f'attachment; filename= "{filename}"'},
            )

        pagination_params = self.get_pagination_params()

        search_query = get_base_entries_search_query(**search_params)
        search_query = get_base_paginate_query(search_query, **pagination_params)
        search_query = get_base_entries_sort_query(search_query, **search_params)

        response = get_search_response(search_query)
        search_results = response["hits"]["hits"]

        data = self.hydrate(search_results)
        serialized_data = self.serialize_search_results(
            search_results, data, **search_params, **pagination_params
        )
        serialized_data = [
            dictionary_entry["entry"] for dictionary_entry in serialized_data
        ]

        return Response(
            data=serialized_data,
            headers={"Content-Disposition": f'attachment; filename= "{filename}"'},
        )
