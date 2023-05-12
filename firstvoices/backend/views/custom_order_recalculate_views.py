from celery.result import AsyncResult
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import CustomOrderRecalculationPreviewResult, Site
from backend.tasks.alphabet_tasks import recalculate_custom_order_preview


class CustomOrderRecalculatePreviewView(APIView):
    # TODO: Add permission classes, superadmin only
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @staticmethod
    def get(request, site_slug: str):
        result = (
            CustomOrderRecalculationPreviewResult.objects.filter(site__slug=site_slug)
            .order_by("-date")
            .first()
        )
        if result:
            return Response({"recalculation_results": result.result}, status=200)
        else:
            return Response(
                {"message": "No recalculation results found for this site."}, status=404
            )

    @staticmethod
    def post(request, site_slug: str):
        try:
            recalculation_results: AsyncResult = (
                recalculate_custom_order_preview.apply_async((site_slug,))
            )

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
