from rest_framework import serializers

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.serializers.fields import SiteHyperlinkedIdentityField


class IgnoredCharacterSerializer(serializers.ModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:ignored_characters-detail")

    class Meta:
        model = IgnoredCharacter
        fields = ["url", "id", "title"]


class CharacterVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterVariant
        fields = ["title"]


class CharacterDetailSerializer(serializers.ModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:characters-detail")
    variants = CharacterVariantSerializer(many=True)

    class Meta:
        model = Character
        fields = [
            "url",
            "id",
            "title",
            "sort_order",
            "approximate_form",
            "notes",
            "variants",
            # related dictionary entries will be added in a future PR
            # "related_dictionary_entries",
        ]
