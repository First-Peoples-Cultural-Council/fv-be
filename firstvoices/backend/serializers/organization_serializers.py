from backend.models import Organization
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_timestamp_fields,
)


class OrganizationSerializer(WritableSiteContentSerializer):
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
