from rest_framework import serializers

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.serializers.base_serializers import (
    BaseSiteContentSerializer,
    UpdateSerializerMixin,
)
from backend.serializers.dictionary_serializers import (
    RelatedDictionaryEntrySerializerMixin,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import RelatedMediaSerializerMixin


class IgnoredCharacterSerializer(BaseSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:ignoredcharacter-detail")

    class Meta:
        model = IgnoredCharacter
        fields = BaseSiteContentSerializer.Meta.fields


class CharacterVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterVariant
        fields = ["title"]


class CharacterDetailSerializer(
    RelatedDictionaryEntrySerializerMixin,
    RelatedMediaSerializerMixin,
    UpdateSerializerMixin,
    BaseSiteContentSerializer,
):
    url = SiteHyperlinkedIdentityField(read_only=True, view_name="api:character-detail")
    title = serializers.CharField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    approximate_form = serializers.CharField(read_only=True)
    variants = CharacterVariantSerializer(read_only=True, many=True)

    class Meta:
        model = Character
        fields = (
            BaseSiteContentSerializer.Meta.fields
            + (
                "sort_order",
                "approximate_form",
                "note",
                "variants",
            )
            + RelatedMediaSerializerMixin.Meta.fields
            + RelatedDictionaryEntrySerializerMixin.Meta.fields
        )
