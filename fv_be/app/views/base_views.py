from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin


class BaseViewSetMixin(AutoPermissionViewSetMixin):
    """
    Mixin used to override the default list view and enable the use of rules based permissions as defined in a model.
    If this mixin is used, the list view will return all model instances that the user has view permissions on.
    """

    def list(self):
        # Get the list of model UUIDs that the user has view permissions for
        models_uuid_list = [
            model.id
            for model in self.get_queryset()
            if self.request.user.has_perm(
                f"app.view_{model.__class__.__name__.lower()}", model
            )
        ]
        # Create a queryset filtered by the UUID list
        queryset = self.queryset.model.objects.filter(id__in=models_uuid_list)
        # Serialize and return the data
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
