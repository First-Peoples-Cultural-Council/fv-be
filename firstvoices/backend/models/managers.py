from django.db import models

from backend.predicates import utils


class PermissionsManager(models.Manager):
    """
    This custom manager adds additional functionality to filter models based on user permissions. For example the
    get_viewable_for_user function allows the filtering of model objects by the view permissions a user has.
    """

    def get_viewable_for_user(self, user):
        """
        Returns a queryset containing only objects that the given user has permission to view. This
        does not filter related objects.
        """
        return utils.filter_by_viewable(user, self.get_queryset())
