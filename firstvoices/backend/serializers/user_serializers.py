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


class UserLookupField(serializers.Field):
    def to_representation(self, value):
        try:
            user = User.objects.get(email=value)
            return UserDetailSerializer(user).data
        except User.DoesNotExist:
            return None

    def to_internal_value(self, data):
        try:
            user = User.objects.get(email=data)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
