import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models import ImmersionLabel, category, dictionary, part_of_speech
from backend.models.constants import (
    MAX_ACKNOWLEDGEMENTS_PER_ENTRY,
    MAX_AUDIO_PER_ENTRY,
    MAX_CATEGORIES_PER_ENTRY,
    MAX_DOCUMENTS_PER_ENTRY,
    MAX_IMAGES_PER_ENTRY,
    MAX_NOTES_PER_ENTRY,
    MAX_PRONUNCIATIONS_PER_ENTRY,
    MAX_RELATED_ENTRIES_PER_ENTRY,
    MAX_SPELLINGS_PER_ENTRY,
    MAX_TRANSLATIONS_PER_ENTRY,
    MAX_VIDEOS_PER_ENTRY,
)
from backend.models.dictionary import ExternalDictionaryEntrySystem
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    WritableControlledSiteContentSerializer,
    audience_fields,
)
from backend.serializers.category_serializers import LinkedCategorySerializer
from backend.serializers.fields import TextListField
from backend.serializers.media_serializers import (
    AudioSerializer,
    DocumentSerializer,
    ImageSerializer,
    RelatedMediaSerializerMixin,
    VideoSerializer,
)
from backend.serializers.parts_of_speech_serializers import (
    PartsOfSpeechSerializer,
    WritablePartsOfSpeechSerializer,
)
from backend.serializers.validators import MaxInstancesValidator


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
    translations = TextListField(required=False, allow_empty=True)

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

    external_system = serializers.SlugRelatedField(
        slug_field="title",
        queryset=ExternalDictionaryEntrySystem.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )

    external_system_entry_id = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    acknowledgements = TextListField(
        required=False,
        allow_empty=True,
        validators=[
            MaxInstancesValidator(
                field_name="acknowledgements",
                max_instances=MAX_ACKNOWLEDGEMENTS_PER_ENTRY,
            )
        ],
    )
    notes = TextListField(
        required=False,
        allow_empty=True,
        validators=[
            MaxInstancesValidator(field_name="notes", max_instances=MAX_NOTES_PER_ENTRY)
        ],
    )
    pronunciations = TextListField(
        required=False,
        allow_empty=True,
        validators=[
            MaxInstancesValidator(
                field_name="pronunciations", max_instances=MAX_PRONUNCIATIONS_PER_ENTRY
            )
        ],
    )
    alternate_spellings = TextListField(
        required=False,
        allow_empty=True,
        validators=[
            MaxInstancesValidator(
                field_name="alternate_spellings", max_instances=MAX_SPELLINGS_PER_ENTRY
            )
        ],
    )
    translations = TextListField(
        required=False,
        allow_empty=True,
        validators=[
            MaxInstancesValidator(
                field_name="translations", max_instances=MAX_TRANSLATIONS_PER_ENTRY
            )
        ],
    )

    is_immersion_label = serializers.SerializerMethodField(read_only=True)

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add max instance validators to related model m2m fields
        self.fields["categories"].validators.append(
            MaxInstancesValidator(
                field_name="categories", max_instances=MAX_CATEGORIES_PER_ENTRY
            )
        )
        self.fields["related_audio"].validators.append(
            MaxInstancesValidator(
                field_name="related_audio", max_instances=MAX_AUDIO_PER_ENTRY
            )
        )
        self.fields["related_images"].validators.append(
            MaxInstancesValidator(
                field_name="related_images", max_instances=MAX_IMAGES_PER_ENTRY
            )
        )
        self.fields["related_videos"].validators.append(
            MaxInstancesValidator(
                field_name="related_videos", max_instances=MAX_VIDEOS_PER_ENTRY
            )
        )
        self.fields["related_documents"].validators.append(
            MaxInstancesValidator(
                field_name="related_documents", max_instances=MAX_DOCUMENTS_PER_ENTRY
            )
        )
        self.fields["related_dictionary_entries"].validators.append(
            MaxInstancesValidator(
                field_name="related_dictionary_entries",
                max_instances=MAX_RELATED_ENTRIES_PER_ENTRY,
            )
        )

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
                "external_system",
                "external_system_entry_id",
            )
            + RelatedMediaSerializerMixin.Meta.fields
            + RelatedDictionaryEntrySerializerMixin.Meta.fields
        )


class DictionaryEntryDetailWriteResponseSerializer(DictionaryEntryDetailSerializer):
    categories = LinkedCategorySerializer(many=True)
    part_of_speech = PartsOfSpeechSerializer()
    related_audio = AudioSerializer(many=True)
    related_documents = DocumentSerializer(many=True)
    related_images = ImageSerializer(many=True)
    related_videos = VideoSerializer(many=True)
    related_dictionary_entries = DictionaryEntryDetailSerializer(many=True)

    class Meta(DictionaryEntryDetailSerializer.Meta):
        pass
