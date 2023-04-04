from rest_framework import serializers

from firstvoices.backend.models.part_of_speech import PartOfSpeech


class PartsOfSpeechSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source="parent.title", allow_null=True)

    class Meta:
        model = PartOfSpeech
        fields = ["id", "title", "parent"]
