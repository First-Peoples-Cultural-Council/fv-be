from rest_framework import serializers

from backend.models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    msg = serializers.SerializerMethodField()
    authenticated_id = serializers.CharField(source="id")

    def get_msg(self, instance):
        return "if you are seeing this, you made an authenticated request successfully"

    class Meta:
        model = User
        fields = ("authenticated_id", "msg")
