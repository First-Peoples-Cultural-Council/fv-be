from rest_framework import serializers

from backend.models.update_jobs import (
    RollbackJob,
    UpdateJob,
    UpdateJobReport,
    UpdateJobReportRow,
    UpdateJobStatus,
)
from backend.serializers import fields
from backend.serializers.import_job_serializers import (
    ImportJobDetailSerializer,
    ImportJobSerializer,
    ImportReportRowSerializer,
    ImportReportSerializer,
)
from backend.serializers.utils.import_job_utils import check_required_headers


class UpdateReportRowSerializer(ImportReportRowSerializer):
    class Meta:
        model = UpdateJobReportRow
        fields = ImportReportRowSerializer.Meta.fields


class UpdateReportSerializer(ImportReportSerializer):
    error_details = UpdateReportRowSerializer(many=True, source="rows")

    class Meta:
        model = UpdateJobReport
        fields = ImportReportSerializer.Meta.fields


class UpdateJobSerializer(ImportJobSerializer):
    status = fields.EnumLabelField(enum=UpdateJobStatus, read_only=True)
    mode = serializers.SerializerMethodField(read_only=True)
    validation_report = UpdateReportSerializer(read_only=True)

    class Meta:
        model = UpdateJob
        fields = ImportJobSerializer.Meta.fields

    # Note: Added mode field to indicate update mode to keep response consistent
    # can be removed later once both jobs have been separated.
    @staticmethod
    def get_mode(_instance):
        return "update"

    def validate_required_headers(self, headers):
        check_required_headers(headers, update_mode=True)

    def build_url_field(self, field_name, model_class):
        """
        Add our namespace to the view_name
        """
        field_class, field_kwargs = super().build_url_field(field_name, model_class)
        field_kwargs["view_name"] = "api:updatejob-detail"

        return field_class, field_kwargs


class UpdateJobDetailSerializer(UpdateJobSerializer, ImportJobDetailSerializer):
    class Meta:
        model = UpdateJob
        fields = UpdateJobSerializer.Meta.fields + ("media",)


class RollbackJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = RollbackJob
        fields = (
            "id",
            "update_job",
            "status",
            "task_id",
            "message",
            "conflicts",
            "created_by",
            "created",
            "last_modified",
            "last_modified_by",
        )
        read_only_fields = fields
