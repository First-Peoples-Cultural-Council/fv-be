from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import CharField, ListField

from backend.models import Site
from backend.utils.contact_us_utils import get_fallback_emails


class ContactUsSerializer(serializers.ModelSerializer):
    email_list = serializers.SerializerMethodField()

    @staticmethod
    @extend_schema_field(ListField(child=CharField()))
    def get_email_list(obj):
        email_list = []
        for email in obj.contact_email:
            email_list.append(email)
        for user in obj.contact_users.all():
            email_list.append(user.email)

        if len(email_list) == 0:
            email_list = get_fallback_emails()

        return email_list

    class Meta:
        model = Site
        fields = ["email_list"]
