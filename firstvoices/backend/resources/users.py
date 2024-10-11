from django.contrib.auth import get_user_model
from import_export import resources


class UserResource(resources.ModelResource):
    class Meta:
        model = get_user_model()

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip users that already exist."""
        user_exists = get_user_model().objects.filter(email=instance.email).exists()
        if user_exists:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)
