import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models import category, dictionary, part_of_speech
from backend.serializers.base_serializers import (
    LinkedSiteSerializer,
    SiteContentLinkedTitleSerializer,
    WritableControlledSiteContentSerializer,
    audience_fields,
)
from backend.serializers.category_serializers import LinkedCategorySerializer
from backend.serializers.media_serializers import (
    RelatedAudioMinimalSerializer,
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


class AcknowledgementSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.Acknowledgement


class AlternateSpellingSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.AlternateSpelling


class WritableCategorySerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return LinkedCategorySerializer(context=self.context).to_representation(value)


class NoteSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.Note


class PronunciationSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.Pronunciation


class TranslationSerializer(serializers.ModelSerializer):
    class Meta(DictionaryContentMeta):
        model = dictionary.Translation


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
    acknowledgements = AcknowledgementSerializer(
        many=True,
        required=False,
        source="acknowledgement_set",
        default=[]
    )
    alternate_spellings = AlternateSpellingSerializer(
        many=True, required=False, source="alternatespelling_set",
        default=[]
    )
    notes = NoteSerializer(many=True, required=False, source="note_set",
        default=[])
    translations = TranslationSerializer(
        many=True, required=False, source="translation_set",
        default=[]
    )
    part_of_speech = WritablePartsOfSpeechSerializer(
        queryset=part_of_speech.PartOfSpeech.objects.all(),
        required=False,
        allow_null=True,
        default=None
    )
    pronunciations = PronunciationSerializer(
        many=True, required=False, source="pronunciation_set",
        default=[]
    )

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

    def create(self, validated_data):
        acknowledgements = validated_data.pop("acknowledgement_set", [])
        alternate_spellings = validated_data.pop("alternatespelling_set", [])
        notes = validated_data.pop("note_set", [])
        pronunciations = validated_data.pop("pronunciation_set", [])
        translations = validated_data.pop("translation_set", [])

        created = super().create(validated_data)

        for acknowledgement in acknowledgements:
            dictionary.Acknowledgement.objects.create(
                dictionary_entry=created, **acknowledgement
            )

        for alternate_spelling in alternate_spellings:
            dictionary.AlternateSpelling.objects.create(
                dictionary_entry=created, **alternate_spelling
            )

        for note in notes:
            dictionary.Note.objects.create(dictionary_entry=created, **note)

        for pronunciation in pronunciations:
            dictionary.Pronunciation.objects.create(
                dictionary_entry=created, **pronunciation
            )

        for translation in translations:
            dictionary.Translation.objects.create(
                dictionary_entry=created, **translation
            )

        return created

    def update(self, instance, validated_data):
        if "acknowledgement_set" in validated_data:
            dictionary.Acknowledgement.objects.filter(
                dictionary_entry=instance
            ).delete()
            acknowledgements = validated_data.pop("acknowledgement_set", [])
            for acknowledgement in acknowledgements:
                dictionary.Acknowledgement.objects.create(
                    dictionary_entry=instance, **acknowledgement
                )

        if "alternatespelling_set" in validated_data:
            dictionary.AlternateSpelling.objects.filter(
                dictionary_entry=instance
            ).delete()
            alternate_spellings = validated_data.pop("alternatespelling_set", [])
            for alternate_spelling in alternate_spellings:
                dictionary.AlternateSpelling.objects.create(
                    dictionary_entry=instance, **alternate_spelling
                )

        if "note_set" in validated_data:
            dictionary.Note.objects.filter(dictionary_entry=instance).delete()
            notes = validated_data.pop("note_set", [])
            for note in notes:
                dictionary.Note.objects.create(dictionary_entry=instance, **note)

        if "pronunciation_set" in validated_data:
            dictionary.Pronunciation.objects.filter(dictionary_entry=instance).delete()
            pronunciations = validated_data.pop("pronunciation_set", [])
            for pronunciation in pronunciations:
                dictionary.Pronunciation.objects.create(
                    dictionary_entry=instance, **pronunciation
                )

        if "translation_set" in validated_data:
            dictionary.Translation.objects.filter(dictionary_entry=instance).delete()
            translations = validated_data.pop("translation_set", [])
            for translation in translations:
                dictionary.Translation.objects.create(
                    dictionary_entry=instance, **translation
                )

        return super().update(instance, validated_data)

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
        ) + audience_fields


class DictionaryEntryMinimalSerializer(serializers.ModelSerializer):
    site = LinkedSiteSerializer(read_only=True)
    translations = TranslationSerializer(
        many=True, required=False, source="translation_set", read_only=True
    )
    related_audio = RelatedAudioMinimalSerializer(
        many=True, required=False, read_only=True
    )
    related_images = RelatedImageMinimalSerializer(
        many=True, required=False, read_only=True
    )

    class Meta:
        model = dictionary.DictionaryEntry
        fields = (
            "id",
            "title",
            "type",
            "site",
            "translations",
            "related_audio",
            "related_images",
        )
        read_only_fields = ("id", "title", "type")
