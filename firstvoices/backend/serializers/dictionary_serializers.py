from backend.models.part_of_speech import PartOfSpeech
from rest_framework import serializers


class PartsOfSpeechChildrenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartOfSpeech
        fields = ["id", "title"]


class PartsOfSpeechSerializer(serializers.ModelSerializer):
    children = PartsOfSpeechChildrenSerializer(many=True)

    class Meta:
        model = PartOfSpeech
        fields = ["id", "title", "children"]
