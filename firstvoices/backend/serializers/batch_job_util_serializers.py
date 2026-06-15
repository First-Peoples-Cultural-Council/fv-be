from rest_framework import serializers

from backend.models.batch_job_utils import BatchJobReport, BatchJobReportRow


class BatchReportRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchJobReportRow
        fields = ["row_number", "status", "errors"]

    row_number = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    errors = serializers.ListField(child=serializers.CharField(), read_only=True)


class BatchReportSerializer(serializers.ModelSerializer):
    error_details = BatchReportRowSerializer(many=True, source="rows")

    class Meta:
        model = BatchJobReport
        fields = [
            "new_rows",
            "error_rows",
            "updated_rows",
            "error_details",
            "accepted_columns",
            "ignored_columns",
        ]
