import uuid

from rest_framework import serializers

from backend.models import Organization
from backend.models.constants import DEFAULT_TITLE_LENGTH, MAX_EMAIL_LENGTH
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_timestamp_fields,
)


class LabeledValueSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    label = serializers.CharField(
        allow_blank=True, allow_null=False, default="", max_length=DEFAULT_TITLE_LENGTH
    )
    value = serializers.CharField(max_length=DEFAULT_TITLE_LENGTH)

    def to_internal_value(self, data):
        validated = super().to_internal_value(data)
        validated["id"] = str(uuid.uuid4())
        return validated


class EmailItemSerializer(LabeledValueSerializer):
    value = serializers.EmailField(max_length=MAX_EMAIL_LENGTH)


class PhoneNumberItemSerializer(LabeledValueSerializer):
    pass


class URLItemSerializer(LabeledValueSerializer):
    value = serializers.URLField(max_length=DEFAULT_TITLE_LENGTH)


class OrganizationSerializer(WritableSiteContentSerializer):
    emails = EmailItemSerializer(many=True, required=False)
    phone_numbers = PhoneNumberItemSerializer(many=True, required=False)
    url_list = URLItemSerializer(many=True, required=False)

    class Meta:
        model = Organization
        fields = base_timestamp_fields + (
            "id",
            "url",
            "name",
            "site",
            "order",
            "emails",
            "phone_numbers",
            "address",
            "contact_message",
            "url_list",
        )
