from jwt_auth.models import User
from rest_framework import serializers


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Provides detailed information about a user.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
        )
