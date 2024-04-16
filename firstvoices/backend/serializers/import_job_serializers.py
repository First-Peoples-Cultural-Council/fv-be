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
from backend.serializers.utils import get_site_from_context
from backend.serializers.validators import SupportedFileType

CSV_MIME_TYPE = "text/csv"
REQUIRED_HEADERS = ["title", "type"]
VALID_HEADERS = [
    "title",
    "type",
    "translation",
    "audio",
    "image",
    "video",
    "video_embed_link",
    "category",
    "note",
    "acknowledgement",
    "part_of_speech",
    "pronunciation",
    "alt_spelling",
    "visibility",
    "include_on_kids_site",
    "include_in_games",
    "related_entry",
]


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
    run_as_user = serializers.CharField()

    class Meta:
        model = ImportJob
        fields = [
            "id",
            "url",
            "data",
            "validation_result",
            "run_as_user",
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

    def validate_headers(self, valid_headers, input_headers):
        # If any invalid headers are present, raise a warning
        # If any headers are present in the _n variaiton, but their original header is not present in the list
        # before the variation, raise a warning
        # The headers for which the warning has been raise would be ignored while processing

        input_headers = [h.strip().lower() for h in input_headers]

        # First check for the required headers
        if set(REQUIRED_HEADERS) - set(input_headers):
            raise serializers.ValidationError(
                detail={
                    "data": [
                        "CSV file does not have the required headers. Please check and upload again."
                    ]
                }
            )

        valid_headers_present = {s: False for s in valid_headers}
        variation_headers_present = {s: False for s in valid_headers}

        for input_header in input_headers:
            if input_header in valid_headers:
                valid_headers_present[input_header] = True
            else:
                checked = False
                for valid_header in valid_headers:
                    if input_header.startswith(valid_header + "_"):
                        # First check if the first header is present
                        if valid_headers_present[valid_header]:
                            variation_headers_present[valid_header] = True
                    else:
                        print(
                            f"Warning: Original header not found, instead found just a variation. {input_header}"
                        )
                    checked = True
                    break
                if not checked:
                    print(f"Warning: Unknown header {input_header}")

    def create(self, validated_data):
        validated_data["site"] = get_site_from_context(self)
        file = self.create_file(validated_data["data"], File, validated_data["site"])

        try:
            table = tablib.Dataset().load(file.content.read().decode("utf-8-sig"))

            # Validate headers
            # If required headers not present, raise ValidationError
            # else, print warnings for extra or invalid headers
            self.validate_headers(VALID_HEADERS, table.headers)

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

    # def create_validation_report(self, result: Result, import_job):
    #     report = ImportJobReport.objects.create(
    #         site=import_job.site,
    #         total_rows=result.total_rows,
    #         column_headers=result.diff_headers,
    #         totals=result.totals,
    #     )
    #
    #     identifier_field_name = "title"
    #     for row_num, row in enumerate(result.rows):
    #         if row.errors:
    #             title = row.errors[0].row[identifier_field_name]
    #             errors = [err.error.args[0] for err in row.errors]
    #         else:
    #             title = row.object_repr
    #             errors = []
    #
    #         ImportJobReportRow.objects.create(
    #             site=import_job.site,
    #             report=report,
    #             status=row.import_type,
    #             identifier_field=identifier_field_name,
    #             identifier_value=title,
    #             errors=errors,
    #             row_number=row_num,
    #         )
    #
    #     return report
