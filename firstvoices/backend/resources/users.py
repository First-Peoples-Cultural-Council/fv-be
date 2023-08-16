from import_export import resources
from jwt_auth.models import User


class UserResource(resources.ModelResource):
    class Meta:
        model = User

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip users that already exist."""
        user_exists = User.objects.filter(email=instance.email).exists()
        if user_exists:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)
