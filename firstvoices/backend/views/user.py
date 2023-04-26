from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from backend.serializers.user import CurrentUserSerializer


@extend_schema_view(
    retrieve=extend_schema(
        description="A stub response about the current user.",
        responses={
            200: inline_serializer(
                name="InlineUserSerializer",
                fields={
                    "msg": serializers.CharField(),
                    "authenticated_id": serializers.CharField(),
                },
            ),
            403: OpenApiResponse(description="Todo: Not Authorized"),
        },
    ),
)
class UserViewSet(viewsets.GenericViewSet):
    http_method_names = ["get"]

    serializer_class = CurrentUserSerializer

    @action(detail=False)
    def current(self, request):
        """
        Get the current user
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
