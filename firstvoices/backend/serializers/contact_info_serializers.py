from backend.models import Organization
from backend.serializers.base_serializers import (
    BaseSiteContentSerializer,
    WritableSiteContentSerializer,
)


class OrganizationSerializer(WritableSiteContentSerializer):
    class Meta:
        model = Organization
        fields = BaseSiteContentSerializer.Meta.fields + (
            "name",
            "order",
            "emails",
            "phone_numbers",
            "address",
            "contact_message",
            "url_list",
        )
