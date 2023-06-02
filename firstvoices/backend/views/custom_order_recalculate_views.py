from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.response import Response

from backend.models import CustomOrderRecalculationResult
from backend.serializers.async_results_serializers import (
    CustomOrderRecalculationResultSerializer,
)
from backend.tasks.alphabet_tasks import (
    recalculate_custom_order,
    recalculate_custom_order_preview,
)
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
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
    create=extend_schema(
        description="Queues a custom order recalculation task for the specified site.",
        responses={
            202: OpenApiResponse(description="Recalculation has been queued."),
            403: OpenApiResponse(
                description="Todo: Action not authorized for this User"
            ),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
)
class CustomOrderRecalculateView(
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    ListViewOnlyModelViewSet,
):
    http_method_names = ["get", "post"]
    serializer_class = CustomOrderRecalculationResultSerializer

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
            recalculation_results = recalculate_custom_order.apply_async((site_slug,))

            # Delete any previous results
            CustomOrderRecalculationResult.objects.filter(
                site=site[0], is_preview=False
            ).delete()

            # Save the result to the database
            CustomOrderRecalculationResult.objects.create(
                site=site[0],
                latest_recalculation_result=recalculation_results.get(timeout=360),
                task_id=recalculation_results.task_id,
                is_preview=False,
            )

            return Response({"message": "Recalculation has been queued."}, status=202)

        except recalculate_custom_order_preview.OperationalError:
            raise CeleryError()


@extend_schema_view(
    list=extend_schema(
        description="Returns the most recent custom order recalculation preview results for the specified site. "
        "Preview results are not saved to the database.",
        responses={
            200: CustomOrderRecalculationResultSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
    create=extend_schema(
        description="Queues a custom order recalculation preview task for the specified site. "
        "dictionary-cleanup/preview and dictionary-cleanup/create_preview are the same endpoint.",
        responses={
            202: OpenApiResponse(description="Recalculation preview has been queued."),
            403: OpenApiResponse(
                description="Todo: Action not authorized for this User"
            ),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
)
class CustomOrderRecalculatePreviewView(
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    ListViewOnlyModelViewSet,
):
    http_method_names = ["get", "post"]
    serializer_class = CustomOrderRecalculationResultSerializer

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
            recalculation_results = recalculate_custom_order_preview.apply_async(
                (site_slug,)
            )

            # Delete any previous preview results
            CustomOrderRecalculationResult.objects.filter(
                site=site[0], is_preview=True
            ).delete()

            # Save the result to the database
            CustomOrderRecalculationResult.objects.create(
                site=site[0],
                latest_recalculation_result=recalculation_results.get(timeout=360),
                task_id=recalculation_results.task_id,
                is_preview=True,
            )

            return Response(
                {"message": "Recalculation preview has been queued."}, status=202
            )

        except recalculate_custom_order_preview.OperationalError:
            raise CeleryError()
