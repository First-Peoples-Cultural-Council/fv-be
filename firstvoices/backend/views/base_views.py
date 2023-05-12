from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend import permissions
from backend.models import Site
from backend.permissions import utils


class FVPermissionViewSetMixin(AutoPermissionViewSetMixin):
    """
    Enforces object-level permissions in ``rest_framework.viewsets.ViewSet``,
    deriving the permission type from the particular action to be performed. List results are
    filtered to only include permitted items.

    As with ``rules.contrib.views.AutoPermissionRequiredMixin``, this only works when
    model permissions are registered using ``rules.contrib.models.RulesModelMixin``.
    """

    def get_queryset(self):
        """
        Allows implementing different querysets for list and detail
        """
        if self.action == "list":
            return self.get_list_queryset()
        else:
            return self.get_detail_queryset()

    def get_list_queryset(self):
        """Defaults to basic get_queryset behaviour"""
        return super().get_queryset()

    def get_detail_queryset(self):
        """Defaults to basic get_queryset behaviour"""
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        # apply view permissions
        queryset = utils.filter_by_viewable(request.user, self.get_queryset())

        # paginated response
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        # non-paginated response
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

        # Check if site content is visible. This uses a different permission rule than for viewing the fields on the
        # Site model itself, which are mainly used in site listings. That's why we're checking is_visible_object
        # rather than the model's view permission.
        if permissions.predicates.is_visible_site_object(self.request.user, site[0]):
            return site
        else:
            raise PermissionDenied
