from rest_framework import serializers

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.serializers.dictionary_serializers import DictionaryEntrySummarySerializer
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
    RelatedMediaSerializerMixin, serializers.ModelSerializer
):
    url = SiteHyperlinkedIdentityField(view_name="api:character-detail")
    variants = CharacterVariantSerializer(many=True)
    related_entries = DictionaryEntrySummarySerializer(
        source="related_dictionary_entries", many=True
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
