from rest_framework import serializers

from backend.models.join_request import (
    JoinRequest,
    JoinRequestReason,
    JoinRequestStatus,
)
from backend.serializers import fields
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.user_serializers import UserLookupField


class JoinRequestDetailSerializer(WritableSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:join-request-detail", read_only=True
    )
    user = UserLookupField(required=True, allow_null=False)
    status = fields.EnumField(enum=JoinRequestStatus, required=True, allow_null=False)
    reason = fields.EnumField(enum=JoinRequestReason, required=True, allow_null=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        site = self.context["site"]
        user = attrs["user"]

        if JoinRequest.objects.filter(site=site, user=user).exists():
            raise serializers.ValidationError(
                "A join request for this site and user already exists."
            )
        return attrs

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
