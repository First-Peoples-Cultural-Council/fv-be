from backend.models.join_request import (
    JoinRequest,
    JoinRequestReason,
    JoinRequestStatus,
)
from backend.serializers import fields
from backend.serializers.base_serializers import (
    BaseSiteContentSerializer,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.user_serializers import UserDetailSerializer


class JoinRequestDetailSerializer(BaseSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:join-request-detail")
    user = UserDetailSerializer(read_only=True)
    status = fields.EnumField(enum=JoinRequestStatus)
    reason = fields.EnumField(enum=JoinRequestReason)

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
