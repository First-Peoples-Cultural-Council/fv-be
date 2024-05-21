import tablib
from django.core.exceptions import PermissionDenied
from rest_framework import serializers
from tablib import InvalidDimensions

from backend.models import Membership
from backend.models.constants import AppRole, Role
from backend.models.import_jobs import ImportJob, ImportJobReport, ImportJobReportRow
from backend.models.jobs import JobStatus
from backend.models.media import File
from backend.serializers import fields
from backend.serializers.base_serializers import CreateSiteContentSerializerMixin
from backend.serializers.job_serializers import BaseJobSerializer
from backend.serializers.media_serializers import FileUploadSerializer
from backend.serializers.utils.context_utils import get_site_from_context
from backend.serializers.utils.import_job_utils import (
    check_required_headers,
    validate_headers,
    validate_username,
)
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
        fields = ["total_rows", "diff_headers", "rows", "totals"]


class ImportJobSerializer(CreateSiteContentSerializerMixin, BaseJobSerializer):
    id = serializers.UUIDField(read_only=True)
    data = FileUploadSerializer(
        validators=[SupportedFileType(mimetypes=["text/csv", "text/plain"])],
    )
    run_as_user = serializers.CharField(required=False)

    validation_task_id = serializers.CharField(read_only=True)
    validation_status = fields.EnumField(enum=JobStatus, read_only=True)
    validation_result = ImportReportSerializer(read_only=True)

    class Meta:
        model = ImportJob
        fields = BaseJobSerializer.Meta.fields + (
            "title",
            "mode",
            "validation_result",
            "run_as_user",
            "data",
            "validation_task_id",
            "validation_status",
        )

    def validate(self, attrs):
        site = get_site_from_context(self)
        user = self.context["request"].user
        memberships = Membership.objects.filter(user=user)

        run_as_user_input = attrs.get("run_as_user")
        site_membership = memberships.filter(site=site).first()
        if run_as_user_input:
            if (
                hasattr(user, "app_role")
                and user.app_role
                and user.app_role.role == AppRole.SUPERADMIN
            ):
                pass
            elif site_membership and (
                site_membership.role in [Role.EDITOR, Role.LANGUAGE_ADMIN]
            ):
                # The above condition will only be true if the person is either an editor or lang. admin
                # If so, the response should be 403 since this field is only accessible by superadmins
                raise PermissionDenied(
                    "You don't have permission to use the runAsUser field."
                )
        return super().validate(attrs)

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
            user = None

            if run_as_user:
                user = validate_username(run_as_user)

            entry = ImportJob(
                title=title,
                data=file,
                site=validated_data["site"],
            )
            if mode:
                entry.mode = mode
            if user:
                entry.run_as_user = user

            # Validate the user and then attach the foreign user object
            # and check if the user requesting is a superadmin

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
