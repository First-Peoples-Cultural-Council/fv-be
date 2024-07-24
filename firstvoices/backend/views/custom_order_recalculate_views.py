from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.jobs import CustomOrderRecalculationJob, JobStatus
from backend.serializers.job_serializers import (
    CustomOrderRecalculationJobSerializer,
    CustomOrderRecalculationPreviewJobSerializer,
)
from backend.tasks.alphabet_tasks import recalculate_custom_order
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from firstvoices.celery import link_error_handler


@extend_schema_view(
    list=extend_schema(
        description="A list of all custom order recalculation results for the specified site.",
        responses={
            200: CustomOrderRecalculationJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific custom order recalculation result.",
        responses={
            200: CustomOrderRecalculationJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description="Create and queue a new custom order recalculation job.",
        responses={
            202: CustomOrderRecalculationJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    clear=extend_schema(
        description="Deletes all finished custom order recalculation results for the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
)
class CustomOrderRecalculateJobViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    ModelViewSet,
):
    http_method_names = ["get", "post", "delete"]
    serializer_class = CustomOrderRecalculationJobSerializer
    permission_type_map = {
        **FVPermissionViewSetMixin.permission_type_map,
        "clear": "delete",
    }

    # TODO: Unsure if this code is needed after refactor
    # def initial(self, *args, **kwargs):
    #     if not is_superadmin(self.request.user, None):
    #         raise PermissionDenied
    #     super().initial(*args, **kwargs)

    # def get_view_name(self):
    #     return "Custom Order Recalculation Results"

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            CustomOrderRecalculationJob.objects.filter(site=site, is_preview=False)
            .select_related("site", "created_by", "last_modified_by")
            .order_by("created")
        )

    def perform_create(self, serializer):
        instance = serializer.save(is_preview=False)

        # Queue the recalculation task after model creation
        transaction.on_commit(
            lambda: recalculate_custom_order.apply_async(
                (instance.id,), link_error=link_error_handler.s()
            )
        )

    @action(methods=["delete"], detail=False)
    def clear(self, request, *args, **kwargs):
        site = self.get_validated_site()

        qs = CustomOrderRecalculationJob.objects.filter(
            site=site,
            is_preview=False,
            status__in=[JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED],
        )
        qs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        description="A list of all custom order recalculation preview results for the specified site.",
        responses={
            200: CustomOrderRecalculationPreviewJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific custom order recalculation preview result.",
        responses={
            200: CustomOrderRecalculationPreviewJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description="Create and queue a new custom order recalculation preview job.",
        responses={
            202: CustomOrderRecalculationPreviewJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    clear=extend_schema(
        description="Deletes all finished custom order recalculation preview results for the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
)
class CustomOrderRecalculatePreviewViewSet(
    CustomOrderRecalculateJobViewSet,
):
    serializer_class = CustomOrderRecalculationPreviewJobSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            CustomOrderRecalculationJob.objects.filter(site=site, is_preview=True)
            .select_related("site", "created_by", "last_modified_by")
            .order_by("created")
        )

    def perform_create(self, serializer):
        # Create the model instance with the preview flag set
        instance = serializer.save(is_preview=True)

        # Queue the recalculation task after model creation
        transaction.on_commit(
            lambda: recalculate_custom_order.apply_async(
                (instance.id,), link_error=link_error_handler.s()
            )
        )

    @action(methods=["delete"], detail=False)
    def clear(self, request, *args, **kwargs):
        site = self.get_validated_site()

        qs = CustomOrderRecalculationJob.objects.filter(
            site=site,
            is_preview=True,
            status__in=[JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED],
        )
        qs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
