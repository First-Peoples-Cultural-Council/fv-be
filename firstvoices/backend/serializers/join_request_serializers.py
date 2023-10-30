import logging

from rest_framework import serializers

from backend.models.constants import Role
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
from backend.tasks.send_email_tasks import send_email_task


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

    def create(self, validated_data):
        created = super().create(validated_data)

        self.notify_language_admins(created)

        return created

    @staticmethod
    def notify_language_admins(created):
        logger = logging.getLogger(__name__)
        site_language_admin_email_list = list(
            created.site.membership_set.filter(role=Role.LANGUAGE_ADMIN).values_list(
                "user__email", flat=True
            )
        )
        if len(site_language_admin_email_list) == 0:
            logger.warning(
                f"No language admins found for site {created.site.slug}. Join request email will not be sent."
            )
        else:
            subject = f"FirstVoices: New join request for {created.site.title}"
            message = (
                f"FirstVoices: You have received a new request to join your site {created.site.title}\n\n"
                f"User: {created.user}\n"
                f"Reason: {created.get_reason_display()}\n"
                f"Reason Note: {created.reason_note}\n\n"
                f"Please visit your FirstVoices site to approve or reject this request.\n\n"
            )
            send_email_task.apply_async(
                (subject, message, site_language_admin_email_list)
            )

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
