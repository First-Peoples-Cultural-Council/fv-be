from rest_framework import serializers

from firstvoices.backend.models.characters import (
    Character,
    CharacterVariant,
    IgnoredCharacter,
)


class CharacterSerializer(serializers.ModelSerializer):
    site = serializers.StringRelatedField()

    class Meta:
        model = Character
        fields = ["id", "title", "sort_order", "approximate_form", "notes", "site"]


class CharacterVariantSerializer(serializers.ModelSerializer):
    site = serializers.StringRelatedField()
    base_character = serializers.StringRelatedField()

    class Meta:
        model = CharacterVariant
        fields = ["id", "title", "base_character", "site"]


class IgnoredCharacterSerializer(serializers.ModelSerializer):
    site = serializers.StringRelatedField()

    class Meta:
        model = IgnoredCharacter
        fields = ["id", "title", "site"]
