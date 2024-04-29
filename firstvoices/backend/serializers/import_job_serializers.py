import tablib
from django.contrib.auth import get_user_model
from rest_framework import serializers
from tablib import InvalidDimensions

from backend.models.import_jobs import ImportJob, ImportJobReport, ImportJobReportRow
from backend.models.media import File
from backend.permissions.predicates.base import is_superadmin
from backend.serializers.base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
)
from backend.serializers.media_serializers import FileUploadSerializer
from backend.serializers.utils.context import get_site_from_context
from backend.serializers.utils.csv_utils import check_required_headers, validate_headers
from backend.serializers.validators import SupportedFileType


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
    CreateSiteContentSerializerMixin, SiteContentLinkedTitleSerializer
):
    id = serializers.UUIDField(read_only=True)
    data = FileUploadSerializer(
        validators=[SupportedFileType(mimetypes=["text/csv", "text/plain"])],
    )
    run_as_user = serializers.CharField(required=False)
    validation_result = ImportReportSerializer(read_only=True)

    class Meta:
        model = ImportJob
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "mode",
            "validation_result",
            "run_as_user",
            "data",
        )

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
            check_required_headers(table.headers)

            # else, print warnings for extra or invalid headers
            validate_headers(table.headers)

            # If the file is valid, create an ImportJob instance and save the file
            title = validated_data.get("title", "")
            mode = validated_data.get("mode", None)
            run_as_user = validated_data.get("run_as_user", None)

            entry = ImportJob(
                title=title,
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
                username_field = user_model.USERNAME_FIELD
                user = user_model.objects.filter(**{username_field: run_as_user})
                if len(user) == 0:
                    raise serializers.ValidationError(
                        detail={
                            "run_as_user": [
                                f"User with the provided {username_field} not found."
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
