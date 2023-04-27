from rest_framework import serializers

from backend.models.dictionary import DictionaryEntry, DictionaryTranslation
from backend.serializers.fields import SiteHyperlinkedIdentityField


class TranslationSerializer(serializers.ModelSerializer):
    part_of_speech = serializers.StringRelatedField()

    class Meta:
        model = DictionaryTranslation
        fields = ("text", "language", "part_of_speech")


class DictionaryEntryDetailSerializer(serializers.HyperlinkedModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:dictionary-detail")
    visibility = serializers.CharField(source="get_visibility_display")
    translations = TranslationSerializer(
        source="dictionary_dictionarytranslation", many=True
    )
    pronunciations = serializers.StringRelatedField(
        source="dictionary_pronunciation", many=True
    )
    notes = serializers.StringRelatedField(
        source="dictionary_dictionarynote", many=True
    )
    alternate_spellings = serializers.StringRelatedField(
        source="dictionary_alternatespelling", many=True
    )
    category = serializers.StringRelatedField()
    site = serializers.StringRelatedField()

    class Meta:
        model = DictionaryEntry
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
            "alternate_spellings",
            "notes",
            "translations",
            "pronunciations",
            "site",
        )
