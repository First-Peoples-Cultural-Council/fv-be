from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin


class FVPermissionViewSetMixin(AutoPermissionViewSetMixin):
    """
    Mixin used to override the default list view and enable the use of rules based permissions as defined in a model.
    If this mixin is used, the list view will return all model instances that the user has view permissions on.
    """

    def list(self, request, *args, **kwargs):
        # Get the model objects a user has view permissions on.
        queryset = self.queryset.model.objects.get_viewable_for_user(request.user)

        # Serialize and return the data
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
