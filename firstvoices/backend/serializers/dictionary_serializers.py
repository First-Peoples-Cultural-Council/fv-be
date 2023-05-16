from rest_framework import serializers

from backend.models import Alphabet, IgnoredCharacter, category, dictionary
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

    def retrieve_model_or_context(self, model_name, site):
        if self.context is None or model_name not in self.context:
            if model_name == "alphabet":
                return Alphabet.objects.filter(site=site).first()
            if model_name == "ignored_characters":
                return IgnoredCharacter.objects.filter(site=site).values_list(
                    "title", flat=True
                )
        else:
            return self.context[model_name]

    def get_split_chars(self, entry):
        alphabet = self.retrieve_model_or_context("alphabet", entry.site)
        ignored_characters = self.retrieve_model_or_context(
            "ignored_characters", entry.site
        )

        if "⚑" in entry.custom_order:
            return []
        else:
            char_list = alphabet.get_character_list(entry.title, self.context)
            has_ignored_char = set(char_list).intersection(set(ignored_characters))
            if has_ignored_char:
                return []
            else:
                return char_list

    def get_split_chars_base(self, entry):
        alphabet = self.retrieve_model_or_context("alphabet", entry.site)
        ignored_characters = self.retrieve_model_or_context(
            "ignored_characters", entry.site
        )
        if "⚑" in entry.custom_order:
            return []
        else:
            # split, check for ignored, then convert title to base characters
            char_list = alphabet.get_character_list(entry.title, self.context)
            has_ignored_char = set(char_list).intersection(set(ignored_characters))
            if has_ignored_char:
                return []
            else:
                base_chars = [
                    alphabet.get_base_form(c, self.context) for c in char_list
                ]
                return base_chars

    @staticmethod
    def get_split_words(entry):
        return entry.title.split(" ")

    def get_split_words_base(self, entry):
        alphabet = self.retrieve_model_or_context("alphabet", entry.site)

        # convert title to base characters
        base_title = alphabet.get_base_form(entry.title, self.context)
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
