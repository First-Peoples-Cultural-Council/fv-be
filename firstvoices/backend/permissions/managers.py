from django.contrib.auth.models import AnonymousUser
from django.db import models

from backend.permissions.filters.base import has_site
from backend.permissions.filters.view import has_visible_site, is_visible_object


class PermissionsManager(models.Manager):
    """
    Abstract manager that adds ability to filter models based on user permissions. Use the appropriate implementation
    for your view permissions.
    """

    # todo: deprecate and remove
    def get_viewable_for_user(self, user):
        """
        Returns a queryset containing only objects that the given user has permission to view. This
        does not filter related objects.
        """
        return self.get_queryset()

    def visible(self, user):
        """
        Returns a queryset containing only objects that the given user has permission to view. This
        does not filter related objects.
        """
        return self.get_queryset().filter(self.visible_as_filter(user))

    def visible_by_site(self, user, site):
        """
        Returns a queryset containing only objects that the given user has permission to view on the
        given site. This does not filter related objects.
        """
        if site is None:
            return self.get_queryset().none()

        return self.get_queryset().filter(self.visible_as_filter(user, site))

    def visible_as_filter(self, user, site=None):
        """
        Returns a Q object representing the visible permissions. Base classes must implement this method.
        """
        # todo: automatically determine which filter to use here if possible (based on declared view permission in meta)
        raise NotImplementedError()


class SiteContentPermissionsManager(PermissionsManager):
    """
    Model manager that adds ability to filter models to match the has_visible_site permission.
    """

    def visible_as_filter(self, user=AnonymousUser(), site=None):
        q = has_visible_site(user)
        if site is not None:
            q &= has_site(site)
        return q


class ControlledSiteContentPermissionsManager(PermissionsManager):
    """
    Model manager that adds ability to filter models to match the is_visible_object permission.
    """

    def visible_as_filter(self, user=AnonymousUser(), site=None):
        q = is_visible_object(user)
        if site is not None:
            q &= has_site(site)
        return q
