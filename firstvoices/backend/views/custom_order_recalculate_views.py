import rules
from celery.result import AsyncResult
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from rest_framework.exceptions import server_error
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import CustomOrderRecalculationPreviewResult, Site
from backend.tasks.alphabet_tasks import recalculate_custom_order_preview


class CustomOrderRecalculatePreviewView(APIView):
    CURRENT_TASK_STATUS_KEY = "preview_current_task_status"
    LATEST_RECALCULATION_DATE_KEY = "latest_recalculation_date"
    LATEST_RECALCULATION_RESULT_KEY = "latest_recalculation_result"

    task_id = None

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

        result = (
            CustomOrderRecalculationPreviewResult.objects.filter(site__slug=site_slug)
            .order_by("-date")
            .first()
        )

        # If there is a task_id, check the status of the task and add it to the response
        if self.task_id:
            async_result = AsyncResult(self.task_id)
            preview_info = {self.CURRENT_TASK_STATUS_KEY: async_result.status}
        else:
            preview_info = {self.CURRENT_TASK_STATUS_KEY: "Not started."}

        # If there is a result, add it to the response
        if result:
            preview_info[self.LATEST_RECALCULATION_DATE_KEY] = result.date
            preview_info[self.LATEST_RECALCULATION_RESULT_KEY] = result.result
        else:
            preview_info[self.LATEST_RECALCULATION_DATE_KEY] = None
            preview_info[self.LATEST_RECALCULATION_RESULT_KEY] = {}

        return Response(preview_info, status=200)

    def post(self, request, site_slug: str):
        # Check Superadmin status
        self.check_permission(request)

        # Check that the site exists
        try:
            site = Site.objects.get(slug=site_slug)
        except ObjectDoesNotExist:
            raise Http404

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
                {"message": "Recalculation preview has been queued."}, status=201
            )

        except recalculate_custom_order_preview.OperationalError:
            raise server_error()
