from rest_framework import serializers

from backend.models.join_request import JoinRequest
from backend.serializers.base_serializers import (
    BaseSiteContentSerializer,
    UserDetailFieldMixin,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField


class JoinRequestDetailSerializer(UserDetailFieldMixin, BaseSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:join-request-detail")
    status = serializers.CharField(source="get_status_display")
    reason = serializers.CharField(source="get_reason_display")

    class Meta:
        model = JoinRequest
        fields = base_timestamp_fields + (
            "id",
            "url",
            "site",
            "user",
            "status",
            "reason",
            "reason_note",
        )
