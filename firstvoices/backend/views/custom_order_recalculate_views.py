from rest_framework.decorators import action
from rest_framework.response import Response

from backend.models import CustomOrderRecalculationResult
from backend.serializers.async_results_serializers import (
    CustomOrderRecalculationPreviewResultSerializer,
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


class CustomOrderRecalculateViewset(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, ListViewOnlyModelViewSet
):
    http_method_names = ["get", "post"]
    serializer_class = CustomOrderRecalculationResultSerializer

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

            return Response({"message": "Recalculation has been queued."}, status=201)

        except recalculate_custom_order_preview.OperationalError:
            raise CeleryError()

    @action(
        methods=["get"],
        detail=False,
        url_path="preview",
        url_name="preview",
        serializer_class=CustomOrderRecalculationPreviewResultSerializer,
    )
    def get_preview(self, request, *args, **kwargs):
        site = self.get_validated_site()
        if site.count() > 0:
            queryset = CustomOrderRecalculationResult.objects.filter(
                site__slug=site[0].slug, is_preview=True
            ).order_by("-latest_recalculation_date")
        else:
            queryset = CustomOrderRecalculationResult.objects.none()

        serializer = CustomOrderRecalculationPreviewResultSerializer(
            queryset, many=True
        )
        return Response(serializer.data, status=200)

    @get_preview.mapping.post
    @action(detail=False)
    def create_preview(self, request, *args, **kwargs):
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
                {"message": "Recalculation preview has been queued."}, status=201
            )

        except recalculate_custom_order_preview.OperationalError:
            raise CeleryError()
