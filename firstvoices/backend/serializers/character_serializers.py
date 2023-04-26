from rest_framework import serializers

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.serializers.fields import SiteHyperlinkedIdentityField


class IgnoredCharacterSerializer(serializers.ModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:ignored_characters-detail")
    site = serializers.StringRelatedField()

    class Meta:
        model = IgnoredCharacter
        fields = ["url", "id", "title", "site"]


class CharacterVariantSerializer(serializers.ModelSerializer):
    site = serializers.StringRelatedField()

    class Meta:
        model = CharacterVariant
        fields = ["id", "title", "base_character", "site"]


class CharacterDetailSerializer(serializers.ModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:characters-detail")
    site = serializers.StringRelatedField()
    # variants = CharacterVariantSerializer(many=True, read_only=True)

    # TODO: Add related characters

    class Meta:
        model = Character
        fields = [
            "url",
            "id",
            "title",
            "sort_order",
            "approximate_form",
            "notes",
            "site",
        ]
