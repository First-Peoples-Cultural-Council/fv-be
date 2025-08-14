from rest_framework import serializers

from backend.models import MTDExportJob
from backend.models.jobs import JobStatus
from backend.serializers import fields


class MTDExportJobSerializer(serializers.ModelSerializer):
    status = fields.EnumLabelField(enum=JobStatus, read_only=True)
    task_id = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)

    class Meta:
        model = MTDExportJob
        fields = (
            "created",
            "last_modified",
            "id",
            "site",
            "status",
            "task_id",
            "message",
        )
