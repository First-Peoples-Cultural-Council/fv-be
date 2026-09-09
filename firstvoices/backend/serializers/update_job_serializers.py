from rest_framework import serializers

from backend.serializers.import_job_serializers import (
    ImportJobDetailSerializer,
    ImportJobSerializer,
)
from backend.serializers.utils.import_job_utils import check_required_headers


class UpdateJobSerializer(ImportJobSerializer):
    mode = serializers.CharField(read_only=True)

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
    pass
