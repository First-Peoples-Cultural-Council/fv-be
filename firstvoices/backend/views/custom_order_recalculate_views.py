from celery.result import AsyncResult
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import CustomOrderRecalculationPreviewResult, Site
from backend.tasks.alphabet_tasks import recalculate_custom_order_preview


class CustomOrderRecalculatePreviewView(APIView):
    task_id = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm("has_superadmin_access"):
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, site_slug: str):
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
            preview_info = {"recalculate_preview_task_status": async_result.status}
        else:
            preview_info = {"recalculate_preview_task_status": "Not started."}

        # If there is a result, add it to the response
        if result:
            preview_info["last_recalculation_date"] = result.date
            preview_info["last_recalculation_result"] = result.result
        else:
            preview_info["last_recalculation_date"] = None
            preview_info["last_recalculation_result"] = {}

        return Response(preview_info, status=200)

    def post(self, request, site_slug: str):
        try:
            recalculation_results = recalculate_custom_order_preview.apply_async(
                (site_slug,)
            )
            self.task_id = recalculation_results.task_id

            site = Site.objects.get(slug=site_slug)
            CustomOrderRecalculationPreviewResult.objects.create(
                site=site, result=recalculation_results.get(timeout=360)
            )

            return Response(
                {"message": "Successfully saved recalculation results"}, status=201
            )

        except recalculate_custom_order_preview.OperationalError as err:
            # log this meaningfully, or just don't catch it
            print(err)
            return Response(
                {"message": "An error occurred while dispatching remote task"},
                status=503,
            )
