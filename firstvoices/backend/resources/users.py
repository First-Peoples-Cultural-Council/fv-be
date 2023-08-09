from import_export import resources
from jwt_auth.models import User


class UserResource(resources.ModelResource):
    class Meta:
        model = User
