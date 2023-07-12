from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.models.dictionary import DictionaryEntry
from backend.serializers.base_serializers import UpdateSerializerMixin
from backend.serializers.dictionary_serializers import DictionaryEntrySummarySerializer
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import (
    RelatedMediaSerializerMixin,
    RelatedMediaUpdateSerializerMixin,
)
from backend.serializers.validators import SameSite


class IgnoredCharacterSerializer(serializers.ModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:ignoredcharacter-detail")

    class Meta:
        model = IgnoredCharacter
        fields = ["url", "id", "title"]


class CharacterVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterVariant
        fields = ["title"]


class CharacterDetailSerializer(
    RelatedMediaSerializerMixin, UpdateSerializerMixin, serializers.ModelSerializer
):
    url = SiteHyperlinkedIdentityField(read_only=True, view_name="api:character-detail")
    title = serializers.CharField(read_only=True)
    variants = CharacterVariantSerializer(read_only=True, many=True)
    related_entries = DictionaryEntrySummarySerializer(
        source="related_dictionary_entries", many=True, read_only=True
    )

    class Meta:
        model = Character
        fields = RelatedMediaSerializerMixin.Meta.fields + (
            "url",
            "id",
            "title",
            "sort_order",
            "approximate_form",
            "note",
            "variants",
            "related_entries",
        )


class CharacterDetailWriteSerializer(
    RelatedMediaUpdateSerializerMixin, CharacterDetailSerializer
):
    related_dictionary_entries = PrimaryKeyRelatedField(
        queryset=DictionaryEntry.objects.all(),
        many=True,
        validators=[SameSite(queryset=DictionaryEntry.objects.all())],
    )

    class Meta(CharacterDetailSerializer.Meta):
        fields = CharacterDetailSerializer.Meta.fields + ("related_dictionary_entries",)
        write_only_fields = ("related_dictionary_entries",)
