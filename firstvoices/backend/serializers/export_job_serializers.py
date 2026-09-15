from rest_framework import serializers

from backend.models import Category, Person
from backend.models.constants import MAX_EXPORT_JOBS, Visibility
from backend.models.jobs import ExportJob, JobStatus
from backend.serializers.base_serializers import CreateSiteContentSerializerMixin
from backend.serializers.files_serializers import FileSerializer
from backend.serializers.job_serializers import BaseJobSerializer


class ExportJobSerializer(CreateSiteContentSerializerMixin, BaseJobSerializer):
    export_csv = FileSerializer(read_only=True)
    export_params = serializers.JSONField(read_only=True)

    def validate(self, attrs):
        # Ensure that accepted, completed and started jobs created by the same user does not exceed MAX_EXPORT_JOBS
        user = self.context["request"].user
        site = self.context["site"]
        count = ExportJob.objects.filter(
            created_by=user,
            site=site,
            status__in=[JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE],
        ).count()

        if count >= MAX_EXPORT_JOBS:
            raise serializers.ValidationError(
                "You have reached the maximum number of simultaneous export jobs (10). "
                "Please delete completed jobs that you no longer need to allow new export jobs to be created."
            )
        return attrs

    def to_representation(self, obj):
        # ensure that user readable params are displayed rather than ids/enums
        representation = super().to_representation(obj)
        export_params = representation["export_params"]
        if not export_params:
            return representation

        # Get category title, replace category ID in representation only
        if export_params["category_id"]:
            try:
                category = Category.objects.get(id=export_params["category_id"])
            except Category.DoesNotExist:
                category = None
            export_params.pop("category_id", None)
            export_params["category"] = category.title if category else ""

        # Get speaker names
        if export_params["speakers"]:
            export_speakers = Person.objects.filter(id__in=export_params["speakers"])
            export_params["speakers"] = [speaker.name for speaker in export_speakers]

        # Get visibility labels
        if export_params["visibility"]:
            export_params["visibility"] = [
                Visibility(visibility).label
                for visibility in export_params["visibility"]
            ]

        representation["export_params"] = export_params
        return representation

    class Meta:
        model = ExportJob
        fields = BaseJobSerializer.Meta.fields + (
            "export_csv",
            "export_params",
            "row_count",
        )
