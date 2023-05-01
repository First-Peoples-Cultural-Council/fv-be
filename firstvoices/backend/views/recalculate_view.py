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
            remotely_computed_result: AsyncResult = (
                recalculate_custom_sort_order.apply_async(("test-site",), countdown=2)
            )

            return Response(
                {
                    "remotely_computed_result": remotely_computed_result.get(
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
