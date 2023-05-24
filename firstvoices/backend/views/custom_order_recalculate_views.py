import rules
from celery.result import AsyncResult
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import CustomOrderRecalculationPreviewResult, Site
from backend.tasks.alphabet_tasks import (
    recalculate_custom_order,
    recalculate_custom_order_preview,
)


class CustomOrderRecalculatePreviewView(APIView):
    task_id = None

    @staticmethod
    def check_superadmin_status(request):
        if not rules.has_perm("views.has_custom_order_access", request.user):
            raise PermissionDenied()

    def get(self, request, site_slug: str):
        # Check Superadmin status
        self.check_superadmin_status(request)

        result = (
            CustomOrderRecalculationPreviewResult.objects.filter(site__slug=site_slug)
            .order_by("-date")
            .first()
        )

        # If there is no result and no task_id, then there are no recalculation results for this site
        if not self.task_id and not result:
            return Response(
                {"message": "No recalculation results found for this site."}, status=404
            )

        # If there is a task_id, check the status of the task and add it to the response
        if self.task_id:
            async_result = AsyncResult(self.task_id)
            preview_info = {"preview_current_task_status": async_result.status}
        else:
            preview_info = {"preview_current_task_status": "Not started."}

        # If there is a result, add it to the response
        if result:
            preview_info["latest_recalculation_date"] = result.date
            preview_info["latest_recalculation_result"] = result.result
        else:
            preview_info["latest_recalculation_date"] = None
            preview_info["latest_recalculation_result"] = {}

        return Response(preview_info, status=200)

    def post(self, request, site_slug: str):
        # Check Superadmin status
        self.check_superadmin_status(request)

        # Check that the site exists
        try:
            site = Site.objects.get(slug=site_slug)
        except Site.DoesNotExist:
            return Response({"message": "Site not found"}, status=404)

        # Call the recalculation preview task
        try:
            recalculation_results = recalculate_custom_order_preview.apply_async(
                (site_slug,)
            )
            self.task_id = recalculation_results.task_id

            CustomOrderRecalculationPreviewResult.objects.create(
                site=site, result=recalculation_results.get(timeout=360)
            )

            return Response(
                {"message": "Successfully saved recalculation results"}, status=201
            )

        except recalculate_custom_order_preview.OperationalError:
            return Response(
                {"message": "An error occurred while dispatching remote task"},
                status=503,
            )


class CustomOrderRecalculateView(APIView):
    task_id = None

    @staticmethod
    def check_superadmin_status(request):
        if not rules.has_perm("views.has_custom_order_access", request.user):
            raise PermissionDenied()

    def get(self, request):
        # Check Superadmin status
        self.check_superadmin_status(request)

        # Return the status of any ongoing recalculation task
        if self.task_id:
            async_result = AsyncResult(self.task_id)
            return Response({"current_task_status": async_result.status})
        else:
            return Response({"current_task_status": "Not started."})

    def post(self, request, site_slug: str):
        # Check Superadmin status
        self.check_superadmin_status(request)

        # Check that the site exists
        try:
            Site.objects.get(slug=site_slug)
        except Site.DoesNotExist:
            return Response({"message": "Site not found"}, status=404)

        # Call the recalculation task
        try:
            recalculation_results = recalculate_custom_order.apply_async((site_slug,))
            self.task_id = recalculation_results.task_id

            return Response(
                {"recalculation_results": recalculation_results.get(timeout=360)}
            )

        except recalculate_custom_order_preview.OperationalError:
            return Response(
                {"message": "An error occurred while dispatching remote task"},
                status=503,
            )
