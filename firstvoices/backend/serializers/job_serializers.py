from collections import OrderedDict

from celery.result import AsyncResult
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models.constants import Visibility
from backend.models.jobs import (
    BulkVisibilityJob,
    CustomOrderRecalculationResult,
    JobStatus,
)
from backend.serializers import fields
from backend.serializers.base_serializers import (
    BaseSiteContentSerializer,
    CreateSiteContentSerializerMixin,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField


class BaseJobSerializer(BaseSiteContentSerializer):
    status = fields.EnumField(enum=JobStatus, read_only=True)
    task_id = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)

    class Meta:
        fields = base_timestamp_fields + (
            "id",
            "url",
            "site",
            "status",
            "task_id",
            "message",
        )


class CustomOrderRecalculationResultSerializer(serializers.ModelSerializer):
    site = serializers.StringRelatedField()
    current_task_status = serializers.SerializerMethodField()
    latest_recalculation_result = serializers.SerializerMethodField()

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_current_task_status(obj):
        async_result = AsyncResult(obj.task_id)
        return async_result.status

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_latest_recalculation_result(obj):
        if (
            hasattr(obj, "latest_recalculation_result")
            and obj.latest_recalculation_result
        ):
            unknown_character_count = obj.latest_recalculation_result.get(
                "unknown_character_count", 0
            )
            updated_entries = obj.latest_recalculation_result["updated_entries"]
        else:
            unknown_character_count = 0
            updated_entries = []

        ordered_result = OrderedDict(
            {
                "unknown_character_count": unknown_character_count,
                "updated_entries": [],
            }
        )

        for entry in updated_entries:
            ordered_entry = OrderedDict(
                {
                    "title": entry["title"],
                    "cleaned_title": entry["cleaned_title"],
                    "is_title_updated": entry["is_title_updated"],
                    "previous_custom_order": entry["previous_custom_order"],
                    "new_custom_order": entry["new_custom_order"],
                }
            )
            ordered_result["updated_entries"].append(ordered_entry)

        return ordered_result

    class Meta:
        model = CustomOrderRecalculationResult
        fields = [
            "site",
            "current_task_status",
            "latest_recalculation_date",
            "latest_recalculation_result",
        ]


class CustomOrderRecalculationPreviewResultSerializer(
    CustomOrderRecalculationResultSerializer
):
    current_preview_task_status = serializers.SerializerMethodField()
    latest_recalculation_preview_result = serializers.JSONField(
        source="latest_recalculation_result"
    )
    latest_recalculation_preview_date = serializers.DateTimeField(
        source="latest_recalculation_date"
    )

    @extend_schema_field(OpenApiTypes.STR)
    def get_current_preview_task_status(self, obj):
        return self.get_current_task_status(obj)

    class Meta:
        model = CustomOrderRecalculationResult
        fields = [
            "site",
            "current_preview_task_status",
            "latest_recalculation_preview_date",
            "latest_recalculation_preview_result",
        ]


class BulkVisibilityJobSerializer(CreateSiteContentSerializerMixin, BaseJobSerializer):
    url = SiteHyperlinkedIdentityField(
        read_only=True, view_name="api:bulk-visibility-detail"
    )
    from_visibility = fields.EnumField(enum=Visibility)
    to_visibility = fields.EnumField(enum=Visibility)

    def validate(self, attrs):
        from_visibility = attrs.get("from_visibility")
        to_visibility = attrs.get("to_visibility")

        if from_visibility == to_visibility:
            raise serializers.ValidationError(
                "'from_visibility' and 'to_visibility' must be different."
            )

        if abs(from_visibility - to_visibility) != 10:
            raise serializers.ValidationError(
                "The difference between 'from_visibility' and 'to_visibility' must be exactly 1 step."
            )

        return super().validate(attrs)

    class Meta:
        model = BulkVisibilityJob
        fields = BaseJobSerializer.Meta.fields + ("from_visibility", "to_visibility")
