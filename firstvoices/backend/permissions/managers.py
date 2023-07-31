from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from . import filters


class PermissionsManager(models.Manager):
    """
    Model manager that adds the ability to apply a custom query filter, suitable for enforcing view permissions.
    A function that returns a Q object must be configured on the model using the `view_permission_filter` property.
    If using the RulesModel features, you can automatically set that property to match the `rules_permissions`
    configuration by using the `PermissionFilterMixin`.
    """

    def visible(self, user):
        """
        Returns a queryset containing only objects that the given user has permission to view. This
        does not filter related objects.
        """
        return self.get_queryset().filter(self.visible_as_filter(user)).distinct()

    def visible_as_filter(self, user=AnonymousUser()):
        """
        Returns a Q object representing the visible permissions. This does not filter related objects. Note that this
        can result in duplicate results and should be used with a distinct() clause.
        """
        if hasattr(self.model, "view_permission_filter"):
            return self.model.view_permission_filter(user)
        else:
            raise ImproperlyConfigured(
                "Model [%s] does not have a view_permission_filter configured"
                % self.model.__name__
            )


class PermissionFilterMixin:
    @classmethod
    def preprocess_rules_permissions(cls, perms):
        """
        Extends the RulesModel features to autodiscover a query filter that matches the declared view permission.
        Filter will be added as a class property called view_permission_filter, which is used by the PermissionsManager.

        Query filters must be created in the filters package and have the same name as their equivalent predicate.
        """
        if "view" in perms:
            view_perm_name = perms["view"].name

            if hasattr(filters, view_perm_name):
                cls.view_permission_filter = getattr(filters, view_perm_name)
            else:
                raise ImproperlyConfigured(
                    "Could not find an equivalent query filter for configured permission [{}] in {}".format(
                        view_perm_name, cls.__name__
                    )
                )
