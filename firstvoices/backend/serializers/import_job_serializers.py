import logging

import tablib
from django.contrib.auth import get_user_model
from rest_framework import serializers
from tablib import InvalidDimensions

from backend.models.import_jobs import ImportJob, ImportJobReport, ImportJobReportRow
from backend.models.media import File
from backend.permissions.predicates.base import is_superadmin
from backend.serializers.base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentUrlMixin,
)
from backend.serializers.media_serializers import FileUploadSerializer
from backend.serializers.utils import get_site_from_context, validate_headers
from backend.serializers.validators import SupportedFileType

CSV_MIME_TYPE = "text/csv"


class ImportReportRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportJobReportRow
        fields = ["row_number", "status", "errors"]

    row_number = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    errors = serializers.ListField(child=serializers.CharField(), read_only=True)


class ImportReportSerializer(serializers.ModelSerializer):
    total_rows = serializers.IntegerField(read_only=True)
    diff_headers = serializers.ListField(child=serializers.CharField(), read_only=True)
    rows = ImportReportRowSerializer(many=True, read_only=True)
    totals = serializers.JSONField(read_only=True)

    class Meta:
        model = ImportJobReport
        fields = ["total_rows", "diff_headers", "totals"]


class ImportJobSerializer(
    CreateSiteContentSerializerMixin, SiteContentUrlMixin, serializers.ModelSerializer
):
    logger = logging.getLogger(__name__)

    id = serializers.UUIDField(read_only=True)
    data = FileUploadSerializer(
        validators=[SupportedFileType(mimetypes=[CSV_MIME_TYPE, "text/plain"])],
    )

    validation_result = ImportReportSerializer(read_only=True)
    run_as_user = serializers.CharField(required=False)

    class Meta:
        model = ImportJob
        fields = [
            "id",
            "url",
            "description",
            "validation_result",
            "run_as_user",
            "data",
        ]

    def create_file(self, file_data, filetype, site):
        user = self.context["request"].user
        file = filetype(
            content=file_data,
            site=site,
            created_by=user,
            last_modified_by=user,
        )
        file.save()
        return file

    def create(self, validated_data):
        validated_data["site"] = get_site_from_context(self)
        file = self.create_file(validated_data["data"], File, validated_data["site"])

        try:
            table = tablib.Dataset().load(
                file.content.read().decode("utf-8-sig"), format="csv"
            )

            # Validate headers
            # If required headers not present, raise ValidationError
            # else, print warnings for extra or invalid headers
            validate_headers(table.headers)

            # If the file is valid, create an ImportJob instance and save the file
            description = validated_data.get("description", "")
            mode = validated_data.get("mode", None)
            run_as_user = validated_data.get("run_as_user", None)

            entry = ImportJob(
                description=description,
                data=file,
                site=validated_data["site"],
            )
            if mode:
                entry.mode = mode

            # Validate the user and then attach the foreign user object
            # and check if the user requesting is a superadmin
            if run_as_user:
                if not is_superadmin(self.context["request"].user, None):
                    # Only superadmins can use this field
                    raise serializers.ValidationError(
                        detail={
                            "run_as_user": [
                                "This field can only be used by superadmins."
                            ]
                        }
                    )
                user_model = get_user_model()
                user = user_model.objects.filter(email=run_as_user)
                if len(user) == 0:
                    raise serializers.ValidationError(
                        detail={
                            "run_as_user": ["User with the provided email not found."]
                        }
                    )
                if len(user) > 1:
                    raise serializers.ValidationError(
                        detail={
                            "run_as_user": [
                                "More than 1 user with the provided email found."
                            ]
                        }
                    )
                entry.run_as_user = user[0]

            entry.save()
            return entry
        except InvalidDimensions:
            raise serializers.ValidationError(
                detail={
                    "data": [
                        "CSV file has invalid dimensions. The size of a column or row doesn't fit the table dimensions."
                    ]
                }
            )
        except Exception as e:
            raise e