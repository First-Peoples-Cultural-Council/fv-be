import rules
from celery.result import AsyncResult
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import CustomOrderRecalculationPreviewResult, Site
from backend.serializers.async_results_serializers import (
    CustomOrderRecalculationPreviewResultDetailSerializer,
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


class CustomOrderRecalculateView(APIView):
    tasks = []

    @staticmethod
    def check_permission(request):
        if not rules.has_perm("views.has_custom_order_access", request.user):
            raise PermissionDenied()

    def get(self, request, site_slug: str):
        # Check Superadmin status
        self.check_permission(request)

        # Check that the site exists
        try:
            Site.objects.get(slug=site_slug)
        except ObjectDoesNotExist:
            raise Http404

        # Return the status of any ongoing recalculation task
        for task in self.tasks:
            if task["site_slug"] == site_slug:
                async_result = AsyncResult(task["task_id"])
                return Response(
                    {"current_recalculation_task_status": async_result.status}
                )
        return Response({"current_recalculation_task_status": "Not started."})

    def post(self, request, site_slug: str):
        # Check Superadmin status
        self.check_permission(request)

        # Check that the site exists
        try:
            Site.objects.get(slug=site_slug)
        except ObjectDoesNotExist:
            raise Http404

        # Call the recalculation task
        try:
            recalculation_results = recalculate_custom_order.apply_async((site_slug,))
            task = {"task_id": recalculation_results.task_id, "site_slug": site_slug}
            self.tasks.append(task)

            return Response(
                {"recalculation_results": recalculation_results.get(timeout=360)},
                status=200,
            )

        except recalculate_custom_order_preview.OperationalError:
            raise CeleryError()
