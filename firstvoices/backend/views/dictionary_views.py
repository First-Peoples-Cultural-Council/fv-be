from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.settings import api_settings

from backend.models.dictionary import DictionaryEntry
from backend.serializers.dictionary_serializers import (
    DictionaryEntryDetailSerializer,
    DictionaryEntryDetailWriteResponseSerializer,
)
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import (
    DictionarySerializerContextMixin,
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)

from ..renderers import BatchExportCSVRenderer
from . import doc_strings
from .utils import get_media_prefetch_list


@extend_schema_view(
    list=extend_schema(
        description="A list of available dictionary entries for the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=DictionaryEntryDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="A dictionary entry from the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=DictionaryEntryDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description="Create a new dictionary entry for the specified site.",
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=DictionaryEntryDetailWriteResponseSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description="Update a dictionary entry on the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=DictionaryEntryDetailWriteResponseSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter, id_parameter],
    ),
    partial_update=extend_schema(
        description="Update a dictionary entry on the specified site. Any omitted fields will be unchanged.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=DictionaryEntryDetailWriteResponseSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter, id_parameter],
    ),
    destroy=extend_schema(
        description="Delete a dictionary entry from the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter, id_parameter],
    ),
)
class DictionaryViewSet(
    SiteContentViewSetMixin,
    DictionarySerializerContextMixin,
    FVPermissionViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    Dictionary entry information.
    """

    serializer_class = DictionaryEntryDetailSerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (
        BatchExportCSVRenderer,
    )

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            DictionaryEntry.objects.filter(site=site)
            .prefetch_related(
                "site",
                "site__language",
                "created_by",
                "last_modified_by",
                "part_of_speech",
                "categories",
                Prefetch(
                    "related_dictionary_entries",
                    queryset=DictionaryEntry.objects.visible(self.request.user)
                    .select_related("site")
                    .prefetch_related(*get_media_prefetch_list(self.request.user)),
                ),
                *get_media_prefetch_list(self.request.user)
            )
            .defer(
                "exclude_from_wotd",
                "legacy_batch_filename",
            )
        )
