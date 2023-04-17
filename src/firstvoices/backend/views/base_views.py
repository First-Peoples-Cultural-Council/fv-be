from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from firstvoices.backend.predicates import utils


class FVPermissionViewSetMixin(AutoPermissionViewSetMixin):
    """
    Enforces object-level permissions in ``rest_framework.viewsets.ViewSet``,
    deriving the permission type from the particular action to be performed. List results are
    filtered to only include permitted items.

    As with ``rules.contrib.views.AutoPermissionRequiredMixin``, this only works when
    model permissions are registered using ``rules.contrib.models.RulesModelMixin``.
    """

    # Method to override the list queryset to implement different querysets for list and retrieve respectively
    def get_list_view_queryset(self):
        return self.get_list_queryset()

    def list(self, request, *args, **kwargs):
        # apply view permissions
        queryset = utils.filter_by_viewable(request.user, self.get_list_view_queryset())

        # paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # serialize and return the data, with context to support hyperlinking
        serializer = self.serializer_class(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)
