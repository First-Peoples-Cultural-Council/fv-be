from rest_framework import serializers

from firstvoices.backend.models.characters import Character


class CharacterSerializer(serializers.ModelSerializer):
    site = serializers.StringRelatedField()

    class Meta:
        model = Character
        fields = ["id", "title", "sort_order", "approximate_form", "notes", "site"]
