import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models import category, dictionary
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import RelatedMediaSerializerMixin
from backend.serializers.site_serializers import LinkedSiteSerializer


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


class DictionaryEntrySummarySerializer(
    RelatedMediaSerializerMixin, SiteContentLinkedTitleSerializer
):
    translations = TranslationSerializer(source="translation_set", many=True)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = dictionary.DictionaryEntry
        fields = (
            (
                "translations",
                "type",
            )
            + RelatedMediaSerializerMixin.Meta.fields
            + SiteContentLinkedTitleSerializer.Meta.fields
        )


class DictionaryEntryDetailSerializer(
    RelatedMediaSerializerMixin, serializers.HyperlinkedModelSerializer
):
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
    site = LinkedSiteSerializer()
    related_entries = DictionaryEntrySummarySerializer(
        source="related_dictionary_entries", many=True
    )
    split_chars = serializers.SerializerMethodField()
    split_chars_base = serializers.SerializerMethodField()
    split_words = serializers.SerializerMethodField()
    split_words_base = serializers.SerializerMethodField()

    logger = logging.getLogger(__name__)

    def get_model_from_context(self, model_name):
        if self.context is not None and model_name in self.context:
            return self.context[model_name]
        else:
            self.logger.error(
                f"({model_name}) context could not be found for view ({self.context['view'].__class__.__name__})"
            )
            return []

    @extend_schema_field(OpenApiTypes.STR)
    def get_split_chars(self, entry):
        alphabet = self.get_model_from_context("alphabet")
        ignored_characters = self.get_model_from_context("ignored_characters")

        if "⚑" in entry.custom_order:
            return []
        else:
            char_list = (
                []
                if alphabet == []
                else alphabet.get_character_list(
                    entry.title,
                    self.context["base_characters"],
                    self.context["character_variants"],
                    self.context["ignorable_characters"],
                )
            )
            has_ignored_char = set(char_list).intersection(set(ignored_characters))
            if has_ignored_char:
                return []
            else:
                return char_list

    @extend_schema_field(OpenApiTypes.STR)
    def get_split_chars_base(self, entry):
        alphabet = self.get_model_from_context("alphabet")
        ignored_characters = self.get_model_from_context("ignored_characters")
        if "⚑" in entry.custom_order:
            return []
        else:
            # split, check for ignored, then convert title to base characters
            char_list = (
                []
                if alphabet == []
                else alphabet.get_character_list(
                    entry.title,
                    self.context["base_characters"],
                    self.context["character_variants"],
                    self.context["ignorable_characters"],
                )
            )
            has_ignored_char = set(char_list).intersection(set(ignored_characters))
            if has_ignored_char:
                return []
            else:
                base_chars = [
                    alphabet.get_base_form(
                        c,
                        self.context["base_characters"],
                        self.context["character_variants"],
                    )
                    for c in char_list
                ]
                return base_chars

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_split_words(entry):
        return entry.title.split(" ")

    @extend_schema_field(OpenApiTypes.STR)
    def get_split_words_base(self, entry):
        alphabet = self.get_model_from_context("alphabet")
        if alphabet == []:
            return entry.title
        # convert title to base characters
        base_title = alphabet.get_base_form(
            entry.title,
            self.context["base_characters"],
            self.context["character_variants"],
        )
        word_list = base_title.split(" ")
        return word_list

    class Meta:
        model = dictionary.DictionaryEntry
        fields = (
            base_timestamp_fields
            + RelatedMediaSerializerMixin.Meta.fields
            + (
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
        )


class WritableRelatedDictionaryEntrySerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return DictionaryEntrySummarySerializer(context=self.context).to_representation(
            value
        )


class RelatedDictionaryEntrySerializerMixin(metaclass=serializers.SerializerMetaclass):
    related_dictionary_entries = WritableRelatedDictionaryEntrySerializer(
        required=False,
        many=True,
        queryset=dictionary.DictionaryEntry.objects.all(),
    )

    def validate(self, attrs):
        related_dictionary_entries = attrs.get("related_dictionary_entries")
        if related_dictionary_entries:
            for entry in related_dictionary_entries:
                if entry.site != self.context["site"]:
                    raise serializers.ValidationError(
                        "Related dictionary entry must be in the same site."
                    )
        return super().validate(attrs)

    class Meta:
        fields = ("related_dictionary_entries",)
