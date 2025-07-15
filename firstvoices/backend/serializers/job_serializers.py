from collections import OrderedDict

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models.constants import Visibility
from backend.models.jobs import BulkVisibilityJob, DictionaryCleanupJob, JobStatus
from backend.serializers import fields
from backend.serializers.base_serializers import (
    BaseSiteContentSerializer,
    CreateSiteContentSerializerMixin,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField


class BaseJobSerializer(BaseSiteContentSerializer):
    status = fields.EnumLabelField(enum=JobStatus, read_only=True)
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


class DictionaryCleanupJobSerializer(
    CreateSiteContentSerializerMixin, BaseJobSerializer
):
    detail_view_name = "api:dictionary-cleanup-detail"

    is_preview = serializers.BooleanField(read_only=True)
    cleanup_result = serializers.SerializerMethodField(read_only=True)

    def get_fields(self):
        fields = super().get_fields()
        # Dynamically assign the view_name to the url field
        fields["url"] = SiteHyperlinkedIdentityField(
            read_only=True, view_name=self.detail_view_name
        )
        return fields

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_cleanup_result(obj):
        if hasattr(obj, "cleanup_result") and obj.cleanup_result:
            unknown_character_count = obj.cleanup_result.get(
                "unknown_character_count", 0
            )
            updated_entries = obj.cleanup_result["updated_entries"]
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
        model = DictionaryCleanupJob
        fields = BaseJobSerializer.Meta.fields + ("is_preview", "cleanup_result")


class DictionaryCleanupPreviewJobSerializer(DictionaryCleanupJobSerializer):
    detail_view_name = "api:dictionary-cleanup-preview-detail"


class BulkVisibilityJobSerializer(CreateSiteContentSerializerMixin, BaseJobSerializer):
    url = SiteHyperlinkedIdentityField(
        read_only=True, view_name="api:bulk-visibility-detail"
    )
    from_visibility = fields.EnumLabelField(enum=Visibility)
    to_visibility = fields.EnumLabelField(enum=Visibility)

    def validate(self, attrs):
        from_visibility = attrs.get("from_visibility")
        to_visibility = attrs.get("to_visibility")
        site = self.context["site"]

        if from_visibility == to_visibility:
            raise serializers.ValidationError(
                "'from_visibility' and 'to_visibility' must be different."
            )

        if site.visibility != from_visibility:
            raise serializers.ValidationError(
                f"'from_visibility' must match the site visibility: {site.get_visibility_display().lower()}."
            )

        if abs(from_visibility - to_visibility) != 10:
            raise serializers.ValidationError(
                "The difference between 'from_visibility' and 'to_visibility' must be exactly 1 step."
            )

        return super().validate(attrs)

    class Meta:
        model = BulkVisibilityJob
        fields = BaseJobSerializer.Meta.fields + ("from_visibility", "to_visibility")
