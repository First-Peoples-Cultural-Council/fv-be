from celery.result import AsyncResult
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.tasks import some_expensive_operation


class ExampleAsyncTaskView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        locally_computed_result = some_expensive_operation("a")

        try:
            # delay 2 seconds and then fire (no reason to, just showing that you can)
            remotely_computed_result: AsyncResult = (
                some_expensive_operation.apply_async(("b",), countdown=2)
            )

            return Response(
                {
                    "locally_computed_result": locally_computed_result,
                    "remotely_computed_result": remotely_computed_result.get(
                        timeout=10
                    ),  # wait max 10s before failing
                }
            )
        except some_expensive_operation.OperationalError as err:
            # log this meaningfully, or just don't catch it
            print(err)
            return Response(
                {"message": "An error occurred while dispatching remote task"},
                status=503,
            )
