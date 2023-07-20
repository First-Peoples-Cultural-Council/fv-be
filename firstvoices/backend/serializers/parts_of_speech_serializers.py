from rest_framework import serializers

from backend.models.part_of_speech import PartOfSpeech


class PartsOfSpeechParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartOfSpeech
        fields = ["id", "title"]


class PartsOfSpeechSerializer(serializers.ModelSerializer):
    parent = PartsOfSpeechParentSerializer()

    class Meta:
        model = PartOfSpeech
        fields = ["id", "title", "parent"]


class WritablePartsOfSpeechSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return PartsOfSpeechSerializer(context=self.context).to_representation(value)
