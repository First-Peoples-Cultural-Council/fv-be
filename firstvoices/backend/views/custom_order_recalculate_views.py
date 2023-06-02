from rest_framework.response import Response

from backend.models import CustomOrderRecalculationPreviewResult
from backend.serializers.async_results_serializers import (
    CustomOrderRecalculationPreviewResultDetailSerializer,
)
from backend.tasks.alphabet_tasks import recalculate_custom_order_preview
from backend.views.base_views import (
    FVPermissionViewSetMixin,
    ListViewOnlyModelViewSet,
    SiteContentViewSetMixin,
)
from backend.views.exceptions import CeleryError


class CustomOrderRecalculatePreviewView(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, ListViewOnlyModelViewSet
):
    http_method_names = ["get", "post"]
    serializer_class = CustomOrderRecalculationPreviewResultDetailSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return CustomOrderRecalculationPreviewResult.objects.filter(
                site__slug=site[0].slug
            ).order_by("-latest_recalculation_date")
        else:
            return CustomOrderRecalculationPreviewResult.objects.none()

    def create(self, request, *args, **kwargs):
        site = self.get_validated_site()
        site_slug = site[0].slug

        # Call the recalculation preview task
        try:
            recalculation_results = recalculate_custom_order_preview.apply_async(
                (site_slug,)
            )

            # Delete any previous results
            CustomOrderRecalculationPreviewResult.objects.filter(site=site[0]).delete()

            # Save the result to the database
            CustomOrderRecalculationPreviewResult.objects.create(
                site=site[0],
                latest_recalculation_result=recalculation_results.get(timeout=360),
                task_id=recalculation_results.task_id,
            )

            return Response(
                {"message": "Recalculation preview has been queued."}, status=201
            )

        except recalculate_custom_order_preview.OperationalError:
            raise CeleryError()
