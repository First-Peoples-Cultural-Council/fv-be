from celery.result import AsyncResult
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.tasks import recalculate_custom_sort_order


class RecalculateView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            # delay 2 seconds and then fire (no reason to, just showing that you can)
            recalculation_results: AsyncResult = (
                recalculate_custom_sort_order.apply_async(("test-site",), countdown=2)
            )

            return Response(
                {
                    "recalculation_results": recalculation_results.get(
                        timeout=10
                    ),  # wait max 10s before failing
                }
            )
        except recalculate_custom_sort_order.OperationalError as err:
            # log this meaningfully, or just don't catch it
            print(err)
            return Response(
                {"message": "An error occurred while dispatching remote task"},
                status=503,
            )
