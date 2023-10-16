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
