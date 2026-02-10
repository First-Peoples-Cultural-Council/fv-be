from backend.models.jobs import ExportJob
from backend.serializers.base_serializers import CreateSiteContentSerializerMixin
from backend.serializers.files_serializers import FileSerializer
from backend.serializers.job_serializers import BaseJobSerializer


class ExportJobSerializer(CreateSiteContentSerializerMixin, BaseJobSerializer):
    export_csv = FileSerializer(read_only=True)

    class Meta:
        model = ExportJob
        fields = BaseJobSerializer.Meta.fields + ("export_csv",)
