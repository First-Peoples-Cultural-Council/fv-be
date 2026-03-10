from rest_framework import serializers

from backend.models.constants import MAX_EXPORT_JOBS
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
        count = ExportJob.objects.filter(
            created_by=user,
            status__in=[JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE],
        ).count()

        if count >= MAX_EXPORT_JOBS:
            raise serializers.ValidationError(
                "You have reached the maximum number of simultaneous export jobs (10). "
                "Please delete completed jobs that you no longer need to allow new export jobs to be created."
            )
        return attrs

    class Meta:
        model = ExportJob
        fields = BaseJobSerializer.Meta.fields + (
            "export_csv",
            "export_params",
        )
