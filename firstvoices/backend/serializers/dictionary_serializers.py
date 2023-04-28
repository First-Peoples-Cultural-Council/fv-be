from rest_framework import serializers

from backend.models import dictionary
from backend.serializers.base_serializers import base_timestamp_fields
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.site_serializers import SiteSummarySerializer


class DictionaryContentMeta:
    fields = ("text",)


class AcknowledgementSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.Acknowledgement


class AlternateSpellingSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.AlternateSpelling


class NoteSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.Note


class PronunciationSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.Pronunciation


class TranslationSerializer(serializers.ModelSerializer):
    part_of_speech = serializers.StringRelatedField()

    class Meta:
        model = dictionary.Translation
        fields = ("text", "language", "part_of_speech")


class DictionaryEntryDetailSerializer(serializers.HyperlinkedModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:dictionary-detail")
    visibility = serializers.CharField(source="get_visibility_display")
    translations = TranslationSerializer(source="translation_set", many=True)
    pronunciations = PronunciationSerializer(source="pronunciation_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    acknowledgements = AcknowledgementSerializer(
        source="acknowledgement_set", many=True
    )
    alternate_spellings = AlternateSpellingSerializer(
        source="alternatespelling_set", many=True
    )
    category = serializers.StringRelatedField()
    site = SiteSummarySerializer()

    class Meta:
        model = dictionary.DictionaryEntry
        fields = base_timestamp_fields + (
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
