from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin


class FVPermissionViewSetMixin(AutoPermissionViewSetMixin):
    """
    Enforces object-level permissions in ``rest_framework.viewsets.ViewSet``,
    deriving the permission type from the particular action to be performed. List results are
    filtered to only include permitted items.

    As with ``rules.contrib.views.AutoPermissionRequiredMixin``, this only works when
    model permissions are registered using ``rules.contrib.models.RulesModelMixin``.
    """

    def list(self, request, *args, **kwargs):
        # Get the list of UUIDs that the user has view permissions for
        allowed_ids = [
            obj.id
            for obj in self.get_queryset()
            if self.request.user.has_perm(
                f"app.view_{obj.__class__.__name__.lower()}", obj
            )
        ]
        # Create a queryset filtered by the UUID list
        queryset = self.queryset.model.objects.filter(id__in=allowed_ids)

        # paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Serialize and return the data, with context to support hyperlinking
        serializer = self.serializer_class(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)
