import os

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, format=None):
        return Response(
            {
                "status": "server is ok",
                "build": os.environ.get("BUILD_STRING", "local"),
                "environment": os.environ.get("ENVIRONMENT_NAME", "local"),
            }
        )
