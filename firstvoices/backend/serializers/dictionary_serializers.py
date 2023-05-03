from rest_framework import serializers

from backend.models import Alphabet, category, dictionary
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    base_timestamp_fields,
)
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


class CategorySerializer(SiteContentLinkedTitleSerializer):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = category.Category


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
    url = SiteHyperlinkedIdentityField(view_name="api:dictionaryentry-detail")
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
    categories = CategorySerializer(many=True)
    site = SiteSummarySerializer()
    base_characters = serializers.SerializerMethodField()
    words_in_phrase = serializers.SerializerMethodField()

    @staticmethod
    def get_base_characters(entry):
        if "⚑" in entry.custom_order:
            return "Due to this entry containing unknown characters, it cannot be used in games."
        else:
            alphabet = Alphabet.objects.filter(site=entry.site).first()
            cs = alphabet.sorter
            character_list = cs.word_as_chars(entry.title)
            for i, char in enumerate(character_list):
                character_list[i] = alphabet.presort_transducer(char).output_string

            return character_list

    @staticmethod
    def get_words_in_phrase(entry):
        if entry.type != "PHRASE":
            return "This entry is not a phrase."
        else:
            alphabet = Alphabet.objects.filter(site=entry.site).first()
            word_list = entry.title.split(" ")
            for i, word in enumerate(word_list):
                word_list[i] = alphabet.presort_transducer(word).output_string
            return word_list

    class Meta:
        model = dictionary.DictionaryEntry
        fields = base_timestamp_fields + (
            "url",
            "id",
            "title",
            "type",
            "custom_order",
            "visibility",
            "categories",
            "exclude_from_games",
            "exclude_from_kids",
            # "related_entries",
            "acknowledgements",
            "alternate_spellings",
            "notes",
            "translations",
            "pronunciations",
            "site",
            "base_characters",
            "words_in_phrase",
        )
