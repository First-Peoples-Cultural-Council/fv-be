import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models import ImmersionLabel, category, dictionary, part_of_speech
from backend.serializers.base_serializers import (
    LinkedSiteMinimalSerializer,
    ReadOnlyVisibilityFieldMixin,
    SiteContentLinkedTitleSerializer,
    WritableControlledSiteContentSerializer,
    audience_fields,
)
from backend.serializers.category_serializers import LinkedCategorySerializer
from backend.serializers.fields import RelatedTextField
from backend.serializers.media_serializers import (
    AudioMinimalSerializer,
    RelatedImageMinimalSerializer,
    RelatedMediaSerializerMixin,
)
from backend.serializers.parts_of_speech_serializers import (
    PartsOfSpeechSerializer,
    WritablePartsOfSpeechSerializer,
)


class DictionaryContentMeta:
    fields = ("id", "text")
    read_only_fields = ("id",)


class WritableCategorySerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return LinkedCategorySerializer(context=self.context).to_representation(value)


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


class DictionaryEntrySummarySerializer(
    RelatedMediaSerializerMixin, SiteContentLinkedTitleSerializer
):
    translations = RelatedTextField(required=False, allow_empty=True)

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
    RelatedDictionaryEntrySerializerMixin,
    RelatedMediaSerializerMixin,
    WritableControlledSiteContentSerializer,
):
    type = serializers.ChoiceField(
        allow_null=False,
        choices=dictionary.TypeOfDictionaryEntry.choices,
        default=dictionary.TypeOfDictionaryEntry.WORD,
    )
    custom_order = serializers.CharField(read_only=True)
    categories = WritableCategorySerializer(
        queryset=category.Category.objects.all(),
        many=True,
        required=False,
    )
    part_of_speech = WritablePartsOfSpeechSerializer(
        queryset=part_of_speech.PartOfSpeech.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )
    notes = RelatedTextField(required=False, allow_empty=True)
    translations = RelatedTextField(required=False, allow_empty=True)
    acknowledgements = RelatedTextField(required=False, allow_empty=True)
    pronunciations = RelatedTextField(required=False, allow_empty=True)
    alternate_spellings = RelatedTextField(required=False, allow_empty=True)

    is_immersion_label = serializers.SerializerMethodField(read_only=True)

    logger = logging.getLogger(__name__)

    def validate(self, attrs):
        # Categories must be in the same site as the dictionary entry
        categories = attrs.get("categories")
        if categories:
            for c in categories:
                if c.site != self.context["site"]:
                    raise serializers.ValidationError(
                        "Related dictionary entry must be in the same site."
                    )
        return super().validate(attrs)

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
        if not alphabet:
            return entry.title
        # convert title to base characters
        base_title = alphabet.get_base_form(
            entry.title,
            self.context["base_characters"],
            self.context["character_variants"],
        )
        word_list = base_title.split(" ")
        return word_list

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_immersion_label(self, entry):
        return ImmersionLabel.objects.filter(dictionary_entry=entry).exists()

    class Meta:
        model = dictionary.DictionaryEntry
        fields = (
            WritableControlledSiteContentSerializer.Meta.fields
            + audience_fields
            + (
                "type",
                "custom_order",
                "categories",
                "acknowledgements",
                "alternate_spellings",
                "notes",
                "translations",
                "part_of_speech",
                "pronunciations",
                "is_immersion_label",
            )
            + RelatedMediaSerializerMixin.Meta.fields
            + RelatedDictionaryEntrySerializerMixin.Meta.fields
        )


class DictionaryEntryDetailWriteResponseSerializer(DictionaryEntryDetailSerializer):
    categories = LinkedCategorySerializer(many=True)
    part_of_speech = PartsOfSpeechSerializer()

    class Meta:
        model = dictionary.DictionaryEntry
        fields = (
            "title",
            "type",
            "visibility",
            "categories",
            "acknowledgements",
            "alternate_spellings",
            "notes",
            "translations",
            "part_of_speech",
            "pronunciations",
            "related_dictionary_entries",
            "related_audio",
            "related_images",
            "related_videos",
            "related_video_links",
        ) + audience_fields


class DictionaryEntryMinimalSerializer(
    ReadOnlyVisibilityFieldMixin, serializers.ModelSerializer
):
    site = LinkedSiteMinimalSerializer(read_only=True)
    translations = RelatedTextField(required=False, allow_empty=True)
    related_audio = AudioMinimalSerializer(many=True, required=False, read_only=True)
    related_images = RelatedImageMinimalSerializer(
        many=True, required=False, read_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove the split_chars_base field from the serializer if the games_flag is not set to True
        if not self.context.get("games_flag"):
            self.fields.pop("split_chars_base")

    class Meta:
        model = dictionary.DictionaryEntry
        fields = (
            "id",
            "created",
            "last_modified",
            "visibility",
            "title",
            "type",
            "site",
            "translations",
            "related_audio",
            "related_images",
            "split_chars_base",
        )
        read_only_fields = ("id", "title", "type")
