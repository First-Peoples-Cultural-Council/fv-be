from rest_framework import serializers

from backend.models import files


class FileSerializer(serializers.ModelSerializer):
    path = serializers.FileField(source="content")

    class Meta:
        model = files.File
        fields = ("path", "mimetype", "size")


class FileUploadSerializer(serializers.FileField):
    def to_representation(self, value):
        return FileSerializer(context=self.context).to_representation(value)
