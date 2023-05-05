from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.models import Site
from backend.predicates import utils


class FVPermissionViewSetMixin(AutoPermissionViewSetMixin):
    """
    Enforces object-level permissions in ``rest_framework.viewsets.ViewSet``,
    deriving the permission type from the particular action to be performed. List results are
    filtered to only include permitted items.

    As with ``rules.contrib.views.AutoPermissionRequiredMixin``, this only works when
    model permissions are registered using ``rules.contrib.models.RulesModelMixin``.
    """

    # Method to override the list queryset to implement different querysets for list and retrieve respectively
    def get_list_queryset(self):
        """
        Defaults to main queryset.
        """
        return self.get_queryset()

    def list(self, request, *args, **kwargs):
        # apply view permissions
        queryset = utils.filter_by_viewable(request.user, self.get_list_queryset())

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


class SiteContentViewSetMixin:
    """
    Provides common methods for handling site content, usually for data models that use the BaseSiteContentModel.
    """

    def get_validated_site(self):
        site_slug = self.kwargs["site_slug"]
        site = Site.objects.filter(slug=site_slug)

        if len(site) == 0:
            raise Http404

        allowed_site = utils.filter_by_viewable(self.request.user, site)
        if len(allowed_site) == 0:
            raise PermissionDenied

        return allowed_site
