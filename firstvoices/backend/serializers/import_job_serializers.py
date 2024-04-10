import logging
import os

import tablib
from import_export.results import Result
from rest_framework import serializers
from tablib import InvalidDimensions

from backend.models.import_jobs import ImportJob, ImportJobReport, ImportJobReportRow
from backend.models.media import File
from backend.resources.dictionary import DictionaryEntryResource
from backend.serializers.base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
)
from backend.serializers.media_serializers import FileUploadSerializer
from backend.serializers.utils import get_site_from_context
from backend.serializers.validators import SupportedFileType


class ImportReportRowSerializer(serializers.Serializer):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = ImportJobReportRow
        fields = ["row_number", "status", "errors"]

    row_number = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    errors = serializers.ListField(child=serializers.CharField(), read_only=True)


class ImportReportSerializer(serializers.Serializer):
    total_rows = serializers.IntegerField(read_only=True)
    diff_headers = serializers.ListField(child=serializers.CharField(), read_only=True)
    rows = ImportReportRowSerializer(many=True, read_only=True)
    # invalid_rows = ImportResultRowSerializer(many=True)   # todo
    totals = serializers.JSONField(read_only=True)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = ImportJobReport
        fields = ["total_rows", "diff_headers", "totals"]


class ImportJobSerializer(
    CreateSiteContentSerializerMixin, SiteContentLinkedTitleSerializer
):
    logger = logging.getLogger(__name__)

    data = FileUploadSerializer(
        validators=[SupportedFileType(mimetypes=["text/csv", "text/plain"])],
    )

    validation_result = ImportReportSerializer(read_only=True)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = ImportJob
        fields = [
            *SiteContentLinkedTitleSerializer.Meta.fields,
            "data",
            "validation_result",
        ]

    def create_file(self, file_data, filetype, site):
        # todo: refactor to share this with the media serializers
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
        uploaded_file = validated_data.pop("data")
        validated_data["data"] = self.create_file(
            uploaded_file, File, validated_data["site"]
        )

        try:
            # todo: experiment with doing a dry run of the import here
            # todo: note that this still uses a hardcoded temp data path instead of the file in the request-- sorry!
            dummy_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../tests/temp_test_import_data",
                "invalid-field.csv",
            )
            with open(dummy_file_path) as f:
                resource = DictionaryEntryResource(site_id=validated_data["site"].id)
                self.logger.info(f"Importing file: {dummy_file_path}")
                table = tablib.import_set(f, format="csv")

            result = resource.import_data(
                dataset=table, raise_errors=False, dry_run=True
            )

            created = super().create(validated_data)

            validation_report = self.create_validation_report(result, created)
            created.validation_result = validation_report
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

        return created

    def create_validation_report(self, result: Result, import_job):
        report = ImportJobReport.objects.create(
            site=import_job.site,
            total_rows=result.total_rows,
            column_headers=result.diff_headers,
            totals=result.totals,
        )

        identifier_field_name = "title"
        for row_num, row in enumerate(result.rows):
            if row.errors:
                title = row.errors[0].row[identifier_field_name]
                errors = [err.error.args[0] for err in row.errors]
            else:
                title = row.object_repr
                errors = []

            ImportJobReportRow.objects.create(
                site=import_job.site,
                report=report,
                status=row.import_type,
                identifier_field=identifier_field_name,
                identifier_value=title,
                errors=errors,
                row_number=row_num,
            )

        return report
