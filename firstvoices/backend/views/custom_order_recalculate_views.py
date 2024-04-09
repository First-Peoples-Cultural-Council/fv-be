from celery.result import AsyncResult
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from backend.models import CustomOrderRecalculationResult
from backend.permissions.predicates import is_superadmin
from backend.serializers.async_results_serializers import (
    CustomOrderRecalculationPreviewResultSerializer,
    CustomOrderRecalculationResultSerializer,
)
from backend.tasks.alphabet_tasks import (
    recalculate_custom_order,
    recalculate_custom_order_preview,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import (
    FVPermissionViewSetMixin,
    ListViewOnlyModelViewSet,
    SiteContentViewSetMixin,
)
from backend.views.exceptions import CeleryError


@extend_schema_view(
    list=extend_schema(
        description="Returns the most recent custom order recalculation results for the specified site.",
        responses={
            200: CustomOrderRecalculationResultSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    create=extend_schema(
        description="Queues a custom order recalculation task for the specified site.",
        responses={
            202: OpenApiResponse(description="Recalculation has been queued."),
            303: OpenApiResponse(
                description="Recalculation is already running. Refer to the redirect-url(location)"
                " in the response headers to get the current status."
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    clear=extend_schema(
        description="Deletes all custom order recalculation results for the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
)
class CustomOrderRecalculateViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    ListViewOnlyModelViewSet,
):
    http_method_names = ["get", "post", "delete"]
    serializer_class = CustomOrderRecalculationResultSerializer
    permission_type_map = {
        **FVPermissionViewSetMixin.permission_type_map,
        "clear": "delete",
    }

    def initial(self, *args, **kwargs):
        if not is_superadmin(self.request.user, None):
            raise PermissionDenied
        super().initial(*args, **kwargs)

    def get_view_name(self):
        return "Custom Order Recalculation Results"

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return CustomOrderRecalculationResult.objects.filter(
                site__slug=site[0].slug, is_preview=False
            ).order_by("-latest_recalculation_date")
        else:
            return CustomOrderRecalculationResult.objects.none()

    def create(self, request, *args, **kwargs):
        site = self.get_validated_site()
        site_slug = site[0].slug

        # Call the recalculation task
        try:
            # Check if preview task for the same site is ongoing
            previous_tasks = CustomOrderRecalculationResult.objects.filter(
                site=site[0], is_preview=False
            )
            running_tasks = 0
            if len(previous_tasks) > 0:
                for task in previous_tasks:
                    status = AsyncResult(task.task_id).status
                    if status == "PENDING":
                        running_tasks += 1

            if running_tasks > 0:
                response = Response(status=303)
                response["Location"] = reverse(
                    "api:dictionary-cleanup-list", kwargs=kwargs
                )
                return response

            recalculate_custom_order.apply_async((site_slug,))
            return Response({"message": "Recalculation has been queued."}, status=202)

        except recalculate_custom_order.OperationalError:
            raise CeleryError()

    @action(methods=["delete"], detail=False)
    def clear(self, request, *args, **kwargs):
        site = self.get_validated_site()
        site_slug = site[0].slug

        qs = CustomOrderRecalculationResult.objects.filter(
            site__slug=site_slug, is_preview=False
        )
        qs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        description="Returns the most recent custom order recalculation preview results for the specified site. "
        "Preview results are not saved to the database.",
        responses={
            200: CustomOrderRecalculationResultSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
        parameters=[site_slug_parameter],
    ),
    create=extend_schema(
        description="Queues a custom order recalculation preview task for the specified site. ",
        responses={
            202: OpenApiResponse(description="Recalculation preview has been queued."),
            303: OpenApiResponse(
                description="Recalculation preview is already running. Refer to the "
                "redirect-url(location) in the response headers to get the "
                "current status."
            ),
            403: OpenApiResponse(
                description="Todo: Action not authorized for this User"
            ),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
        parameters=[site_slug_parameter],
    ),
    clear=extend_schema(
        description="Deletes all custom order recalculation preview results for the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
)
class CustomOrderRecalculatePreviewViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    ListViewOnlyModelViewSet,
):
    http_method_names = ["get", "post", "delete"]
    serializer_class = CustomOrderRecalculationPreviewResultSerializer
    permission_type_map = {
        **FVPermissionViewSetMixin.permission_type_map,
        "clear": "delete",
    }

    def initial(self, *args, **kwargs):
        if not is_superadmin(self.request.user, None):
            raise PermissionDenied
        super().initial(*args, **kwargs)

    def get_view_name(self):
        return "Custom Order Recalculation Preview Results"

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            queryset = CustomOrderRecalculationResult.objects.filter(
                site__slug=site[0].slug, is_preview=True
            ).order_by("-latest_recalculation_date")
        else:
            queryset = CustomOrderRecalculationResult.objects.none()

        return queryset

    def create(self, request, *args, **kwargs):
        site = self.get_validated_site()
        site_slug = site[0].slug

        # Call the recalculation preview task
        try:
            # Check if preview task for the same site is ongoing
            previous_tasks = CustomOrderRecalculationResult.objects.filter(
                site=site[0], is_preview=True
            )
            running_tasks = 0
            if len(previous_tasks) > 0:
                for task in previous_tasks:
                    status = AsyncResult(task.task_id).status
                    if status == "PENDING":
                        running_tasks += 1

            if running_tasks > 0:
                response = Response(status=303)
                response["Location"] = reverse(
                    "api:dictionary-cleanup-preview-list", kwargs=kwargs
                )
                return response

            recalculate_custom_order_preview.apply_async((site_slug,))
            return Response(
                {"message": "Recalculation preview has been queued."}, status=202
            )

        except recalculate_custom_order_preview.OperationalError:
            raise CeleryError()

    @action(methods=["delete"], detail=False)
    def clear(self, request, *args, **kwargs):
        site = self.get_validated_site()
        site_slug = site[0].slug

        qs = CustomOrderRecalculationResult.objects.filter(
            site__slug=site_slug, is_preview=True
        )
        qs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
