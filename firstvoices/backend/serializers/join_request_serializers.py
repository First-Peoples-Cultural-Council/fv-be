import logging

import redis.exceptions
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
from backend.views.utils import get_site_url_from_appjson


class JoinRequestReasonSerializer(serializers.ModelSerializer):
    reason = fields.EnumLabelField(enum=JoinRequestReasonChoices)

    class Meta:
        fields = ("reason",)
        model = JoinRequestReason


class JoinRequestDetailSerializer(WritableSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:joinrequest-detail", read_only=True
    )
    user = UserDetailSerializer(allow_null=False, read_only=True)
    status = fields.EnumLabelField(
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

        self.notify_language_admins(created, reason_values)

        return created

    def validate(self, attrs):
        attrs = super().validate(attrs)
        site = self.context["site"]
        user = self.context["request"].user

        if JoinRequest.objects.filter(site=site, user=user).exists():
            raise serializers.ValidationError(
                "A join request for this site and user already exists."
            )

        if site.membership_set.filter(user=user).exists():
            raise serializers.ValidationError("User is already a member of this site.")

        if not attrs["reasons_set"]:
            raise serializers.ValidationError(
                "A join request must have at least one reason."
            )
        return attrs

    @staticmethod
    def notify_language_admins(created, reason_values):
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
            subject = f"FirstVoices: New membership request for {created.site.title}"
            message = (
                f"You have received a new membership request to join the {created.site.title} language site.\n\n"
                f"User: {created.user}\n"
                f"Reason(s) for joining:\n"
                f"{', '.join([value['reason'].label for value in reason_values])}\n\n"
                f"Message:\n"
                f"{created.reason_note}\n\n"
                f"To take action on this request, please login to FirstVoices and view your pending memberships.\n"
            )
            base_url = get_site_url_from_appjson(created.site)
            if base_url:
                message = (
                    message
                    + f"Visit the {created.site.title} dashboard here: {base_url}dashboard/\n\n"
                )
            else:
                message = message + "\n"

            try:
                send_email_task.apply_async(
                    (subject, message, site_language_admin_email_list)
                )
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Could not queue task. Error: {e}")

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
