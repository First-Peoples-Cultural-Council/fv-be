from rest_framework import serializers

from backend.models import dictionary
from backend.serializers.fields import SiteHyperlinkedIdentityField


class AcknowledgementSerializer(serializers.ModelSerializer):
    class Meta:
        model = dictionary.DictionaryAcknowledgement
        fields = ("text",)


class AlternateSpellingSerializer(serializers.ModelSerializer):
    class Meta:
        model = dictionary.AlternateSpelling
        fields = ("text",)


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = dictionary.DictionaryNote
        fields = ("text",)


class PronunciationSerializer(serializers.ModelSerializer):
    class Meta:
        model = dictionary.Pronunciation
        fields = ("text",)


class TranslationSerializer(serializers.ModelSerializer):
    part_of_speech = serializers.StringRelatedField()

    class Meta:
        model = dictionary.DictionaryTranslation
        fields = ("text", "language", "part_of_speech")


class DictionaryEntryDetailSerializer(serializers.HyperlinkedModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:dictionary-detail")
    visibility = serializers.CharField(source="get_visibility_display")
    translations = TranslationSerializer(
        source="dictionary_dictionarytranslation", many=True
    )
    pronunciations = PronunciationSerializer(
        source="dictionary_pronunciation", many=True
    )
    notes = NoteSerializer(source="dictionary_dictionarynote", many=True)
    acknowledgements = AcknowledgementSerializer(
        source="dictionary_dictionaryacknowledgement", many=True
    )
    alternate_spellings = AlternateSpellingSerializer(
        source="dictionary_alternatespelling", many=True
    )
    category = serializers.StringRelatedField()
    site = serializers.StringRelatedField()

    class Meta:
        model = dictionary.DictionaryEntry
        fields = (
            "url",
            "id",
            "title",
            "type",
            "custom_order",
            "visibility",
            "category",
            "exclude_from_games",
            "exclude_from_kids",
            # "related_entries",
            "acknowledgements",
            "alternate_spellings",
            "notes",
            "translations",
            "pronunciations",
            "site",
        )
