from rest_framework import serializers

from backend.models import Alphabet, category, dictionary
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.site_serializers import SiteSummarySerializer


class DictionaryContentMeta:
    fields = ("id", "text")


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

    class Meta(DictionaryContentMeta):
        model = dictionary.Translation
        fields = DictionaryContentMeta.fields + ("language", "part_of_speech")


class DictionaryEntrySummarySerializer(SiteContentLinkedTitleSerializer):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = dictionary.DictionaryEntry


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
    related_entries = DictionaryEntrySummarySerializer(
        source="related_dictionary_entries", many=True
    )
    split_chars = serializers.SerializerMethodField()
    split_chars_base = serializers.SerializerMethodField()
    split_words = serializers.SerializerMethodField()
    split_words_base = serializers.SerializerMethodField()

    @staticmethod
    def get_split_chars(entry):
        alphabet = Alphabet.objects.filter(site=entry.site).first()
        ignored_characters = alphabet.ignorable_characters.values_list(
            "title", flat=True
        )
        has_ignored_char = any(char in ignored_characters for char in entry.title)
        if "⚑" in entry.custom_order or has_ignored_char:
            return []
        else:
            return alphabet.get_character_list(entry.title)

    @staticmethod
    def get_split_chars_base(entry):
        alphabet = Alphabet.objects.filter(site=entry.site).first()
        ignored_characters = alphabet.ignorable_characters.values_list(
            "title", flat=True
        )
        has_ignored_char = any(char in ignored_characters for char in entry.title)
        if "⚑" in entry.custom_order or has_ignored_char:
            return []
        else:
            # split, then convert title to base characters
            char_list = alphabet.get_character_list(entry.title)
            base_chars = [alphabet.get_base_form(c) for c in char_list]

            return base_chars

    @staticmethod
    def get_split_words(entry):
        return entry.title.split(" ")

    @staticmethod
    def get_split_words_base(entry):
        alphabet = Alphabet.objects.filter(site=entry.site).first()

        # convert title to base characters
        base_title = alphabet.get_base_form(entry.title)
        word_list = base_title.split(" ")

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
            "related_entries",
            "acknowledgements",
            "alternate_spellings",
            "notes",
            "translations",
            "pronunciations",
            "site",
            "split_chars",
            "split_chars_base",
            "split_words",
            "split_words_base",
        )
