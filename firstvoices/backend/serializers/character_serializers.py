from rest_framework import serializers

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.models.dictionary import DictionaryEntry
from backend.serializers.dictionary_serializers import DictionaryEntryDetailSerializer
from backend.serializers.fields import SiteHyperlinkedIdentityField


class IgnoredCharacterSerializer(serializers.ModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:ignored_characters-detail")
    site = serializers.StringRelatedField()

    class Meta:
        model = IgnoredCharacter
        fields = ["url", "id", "title", "site"]


class CharacterVariantSerializer(serializers.ModelSerializer):
    base_character = serializers.StringRelatedField()

    class Meta:
        model = CharacterVariant
        fields = ["id", "title", "base_character"]


class RelatedDictionaryEntrySerializer(serializers.HyperlinkedModelSerializer):
    dictionary_entry = DictionaryEntryDetailSerializer("dictionary_entry")

    class Meta:
        model = DictionaryEntry
        fields = ["dictionary_entry"]


class CharacterDetailSerializer(serializers.ModelSerializer):
    url = SiteHyperlinkedIdentityField(view_name="api:characters-detail")
    site = serializers.StringRelatedField()
    variants = CharacterVariantSerializer(many=True)
    # This related dictionary entries field is a WIP
    # related_dictionary_entries = RelatedDictionaryEntrySerializer(many=True, source="dictionary_entry_links")

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
            "variants",
            # "related_dictionary_entries",
        ]
