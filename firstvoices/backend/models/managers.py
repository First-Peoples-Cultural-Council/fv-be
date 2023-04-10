from django.db import models


class PermissionsManager(models.Manager):
    """
    This custom manager adds additional functionality to filter models based on user permissions. For example the
    get_viewable_for_user function allows the filtering of model objects by the view permissions a user has.
    """

    def get_viewable_for_user(self, user):
        """This function returns a queryset containing model objects that a user has view permissions on."""

        # Get the list of model UUIDs that the user has view permissions for
        models_uuid_list = [
            model.id
            for model in self.get_queryset()
            if user.has_perm(model.get_perm("view"), model)
        ]
        # Return a queryset filtered by the UUID list
        return self.get_queryset().filter(id__in=models_uuid_list)
