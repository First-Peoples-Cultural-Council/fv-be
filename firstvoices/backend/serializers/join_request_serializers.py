from rest_framework import serializers

from backend.models.join_request import (
    JoinRequest,
    JoinRequestReason,
    JoinRequestReasonChoices,
    JoinRequestStatus,
)
from backend.serializers import fields
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.user_serializers import UserDetailSerializer


class JoinRequestReasonSerializer(serializers.ModelSerializer):
    reason = fields.EnumField(enum=JoinRequestReasonChoices)

    class Meta:
        fields = ("reason",)
        model = JoinRequestReason


class JoinRequestDetailSerializer(WritableSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:joinrequest-detail", read_only=True
    )
    user = UserDetailSerializer(allow_null=False, read_only=True)
    status = fields.EnumField(
        enum=JoinRequestStatus,
        allow_null=False,
        default=JoinRequestStatus.PENDING,
        required=False,
        read_only=True,
    )
    reasons = JoinRequestReasonSerializer(
        many=True, required=True, source="reasons_set"
    )

    def create(self, validated_data):
        reason_values = validated_data.pop("reasons_set")
        validated_data["user"] = self.context["request"].user
        created = super().create(validated_data)

        for value in reason_values:
            if JoinRequestReason.objects.filter(
                join_request=created, reason=value["reason"]
            ).exists():
                raise serializers.ValidationError(
                    "A join request cannot have multiple of the same reason."
                )
            else:
                JoinRequestReason.objects.create(
                    join_request=created, reason=value["reason"]
                )

        return created

    def validate(self, attrs):
        attrs = super().validate(attrs)
        site = self.context["site"]
        user = self.context["request"].user

        if JoinRequest.objects.filter(site=site, user=user).exists():
            raise serializers.ValidationError(
                "A join request for this site and user already exists."
            )

        if not attrs["reasons_set"]:
            raise serializers.ValidationError(
                "A join request must have at least one reason."
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
            "reasons",
            "reason_note",
        )
