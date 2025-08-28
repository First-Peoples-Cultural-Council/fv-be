from rest_framework import serializers


class DictionaryExportCsvSerializer(serializers.Serializer):
    csv_export = serializers.SerializerMethodField()

    def get_csv_export(self, obj):
        return obj.content.url

    class Meta:
        fields = (
            # No BaseJob model since we are not creating export jobs ?
            "id",
            # No URL, do we need a model and create instances for each export job ?
            "site",
            "status",
            "task_id",
            "message",
            "failed_rows_csv",
        )
