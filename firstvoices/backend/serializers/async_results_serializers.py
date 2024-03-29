from collections import OrderedDict

from celery.result import AsyncResult
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models.async_results import CustomOrderRecalculationResult


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
