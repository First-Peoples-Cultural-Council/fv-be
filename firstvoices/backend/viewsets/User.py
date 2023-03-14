from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from backend.serializers.User import CurrentUserSerializer


class UserViewSet(viewsets.GenericViewSet):
    http_method_names = ['get']

    serializer_class = CurrentUserSerializer

    @action(detail=False)
    def current(self, request):
        """
        Get the current user
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
