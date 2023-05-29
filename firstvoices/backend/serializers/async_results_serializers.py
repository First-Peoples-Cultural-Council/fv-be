from collections import OrderedDict

from celery.result import AsyncResult
from rest_framework import serializers

from backend.models.async_results import CustomOrderRecalculationPreviewResult


class CustomOrderRecalculationPreviewResultDetailSerializer(
    serializers.ModelSerializer
):
    site = serializers.StringRelatedField()
    current_preview_task_status = serializers.SerializerMethodField()
    latest_recalculation_result = serializers.SerializerMethodField()

    def get_current_preview_task_status(self, obj):
        async_result = AsyncResult(obj.task_id)
        return async_result.status

    def get_latest_recalculation_result(self, obj):
        ordered_result = OrderedDict(
            {
                "unknown_character_count": obj.latest_recalculation_result[
                    "unknown_character_count"
                ],
                "updated_entries": [],
            }
        )

        for entry in obj.latest_recalculation_result["updated_entries"]:
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
        model = CustomOrderRecalculationPreviewResult
        fields = [
            "site",
            "current_preview_task_status",
            "latest_recalculation_date",
            "latest_recalculation_result",
        ]
