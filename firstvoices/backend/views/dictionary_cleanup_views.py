from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.jobs import DictionaryCleanupJob, JobStatus
from backend.serializers.job_serializers import (
    DictionaryCleanupJobSerializer,
    DictionaryCleanupPreviewJobSerializer,
)
from backend.tasks.dictionary_cleanup_tasks import cleanup_dictionary
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from firstvoices.celery import link_error_handler


@extend_schema_view(
    list=extend_schema(
        description="A list of all dictionary cleanup results for the specified site.",
        responses={
            200: DictionaryCleanupJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific dictionary cleanup result.",
        responses={
            200: DictionaryCleanupJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description="Create and queue a new dictionary cleanup job.",
        responses={
            201: DictionaryCleanupJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    clear=extend_schema(
        description="Deletes all finished dictionary cleanup results for the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
)
class DictionaryCleanupJobViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    ModelViewSet,
):
    http_method_names = ["get", "post", "delete"]
    serializer_class = DictionaryCleanupJobSerializer
    permission_type_map = {
        **FVPermissionViewSetMixin.permission_type_map,
        "clear": "delete",
    }
    is_preview = False

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            DictionaryCleanupJob.objects.filter(site=site, is_preview=self.is_preview)
            .select_related("site", "created_by", "last_modified_by")
            .order_by("created")
        )

    def perform_create(self, serializer):
        instance = serializer.save(is_preview=self.is_preview)

        # Queue the cleanup task after model creation
        transaction.on_commit(
            lambda: cleanup_dictionary.apply_async(
                (instance.id,), link_error=link_error_handler.s()
            )
        )

    @action(methods=["post"], detail=False)
    def clear(self, request, *args, **kwargs):
        site = self.get_validated_site()

        qs = DictionaryCleanupJob.objects.filter(
            site=site,
            is_preview=self.is_preview,
            status__in=[JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED],
        )
        qs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        description="A list of all dictionary cleanup preview results for the specified site.",
        responses={
            200: DictionaryCleanupPreviewJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific dictionary cleanup preview result.",
        responses={
            200: DictionaryCleanupPreviewJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description="Create and queue a new dictionary cleanup preview job.",
        responses={
            202: DictionaryCleanupPreviewJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    clear=extend_schema(
        description="Deletes all finished dictionary cleanup preview results for the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
)
class DictionaryCleanupPreviewViewSet(
    DictionaryCleanupJobViewSet,
):
    serializer_class = DictionaryCleanupPreviewJobSerializer
    is_preview = True
