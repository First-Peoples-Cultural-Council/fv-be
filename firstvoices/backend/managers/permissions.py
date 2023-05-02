from django.db import models

from backend.predicates import utils


class PermissionsManager(models.Manager):
    """
    Abstract manager that adds ability to filter models based on user permissions. Use the appropriate implementation
    for your view permissions.
    """

    def get_viewable_for_user(self, user):
        """
        Returns a queryset containing only objects that the given user has permission to view. This
        does not filter related objects.
        """
        return utils.filter_by_viewable(user, self.get_queryset())

    def get_visible_for_user(self, user, sites):
        """
        Returns a queryset containing only objects that the given user has permission to view. This
        does not filter related objects.
        """
        return self.get_queryset().filter(self.get_view_permissions_filter(user, sites))

    def get_view_permissions_filter(self, user, sites=None):
        """
        Base classes must implement the permissions filter.
        """
        raise NotImplementedError()


class SiteContentPermissionsManager(PermissionsManager):
    """
    Model manager that adds ability to filter models to match the is_visible_object permission.
    """

    def get_view_permissions_filter(self, user, sites=None):
        """
                is_visible_object = (
            base.has_public_access_to_obj
            | base.is_at_least_staff_admin
            | base.has_member_access_to_obj
            | base.has_team_access_to_obj
        )
        """
        raise NotImplementedError()
        # if sites is None or empty:
        # nothing?

        # get the user's memberships

        # where: (obj is public and site is public) | (user is at least staff admin) |
        # for each membership: (site.id is X | obj.visibility > (min for membership role) )

        # for has_visible_site:
        # where: (site is public) | (user is at least staff admin) |
        # for each membership: (site.id is X | site.visibility > (min for membership role) )
