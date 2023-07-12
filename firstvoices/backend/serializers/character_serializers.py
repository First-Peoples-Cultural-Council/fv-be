from rest_framework import serializers

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.serializers.base_serializers import UpdateSerializerMixin
from backend.serializers.dictionary_serializers import (
    RelatedDictionaryEntrySerializerMixin,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import RelatedMediaSerializerMixin


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
    RelatedDictionaryEntrySerializerMixin,
    RelatedMediaSerializerMixin,
    UpdateSerializerMixin,
    serializers.ModelSerializer,
):
    url = SiteHyperlinkedIdentityField(read_only=True, view_name="api:character-detail")
    title = serializers.CharField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    approximate_form = serializers.CharField(read_only=True)
    variants = CharacterVariantSerializer(read_only=True, many=True)

    def validate(self, attrs):
        related_dictionary_entries = attrs.get("related_dictionary_entries")
        if related_dictionary_entries:
            for entry in related_dictionary_entries:
                if entry.site != self.context["site"]:
                    raise serializers.ValidationError(
                        "Related dictionary entry must be in the same site as the character."
                    )
        super().validate(attrs)

    class Meta:
        model = Character
        fields = (
            RelatedMediaSerializerMixin.Meta.fields
            + (
                "url",
                "id",
                "title",
                "sort_order",
                "approximate_form",
                "note",
                "variants",
            )
            + RelatedDictionaryEntrySerializerMixin.Meta.fields
        )
