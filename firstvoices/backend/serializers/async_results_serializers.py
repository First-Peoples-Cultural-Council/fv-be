from celery.result import AsyncResult
from rest_framework import serializers

from backend.models.async_results import CustomOrderRecalculationPreviewResult


class CustomOrderRecalculationPreviewResultDetailSerializer(
    serializers.ModelSerializer
):
    site = serializers.StringRelatedField()
    current_preview_task_status = serializers.SerializerMethodField()

    def get_current_preview_task_status(self, obj):
        async_result = AsyncResult(obj.task_id)
        return async_result.status

    class Meta:
        model = CustomOrderRecalculationPreviewResult
        fields = [
            "site",
            "current_preview_task_status",
            "latest_recalculation_date",
            "latest_recalculation_result",
        ]
