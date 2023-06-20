from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    msg = serializers.SerializerMethodField()
    authenticated_id = serializers.CharField(source="id")

    @extend_schema_field(OpenApiTypes.STR)
    def get_msg(self, instance):
        return "if you are seeing this, you made an authenticated request successfully"

    class Meta:
        model = User
        fields = ("authenticated_id", "msg")
