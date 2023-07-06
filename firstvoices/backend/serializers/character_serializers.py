from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.models.dictionary import DictionaryEntry
from backend.serializers.base_serializers import UpdateSerializerMixin
from backend.serializers.dictionary_serializers import DictionaryEntrySummarySerializer
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import RelatedMediaSerializerMixin
from backend.serializers.validators import SameSite, UniqueForSite


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


class CharacterDetailWriteSerializer(CharacterDetailSerializer):
    variants = PrimaryKeyRelatedField(
        write_only=True,
        queryset=CharacterVariant.objects.all(),
        allow_null=True,
        many=True,
        validators=[
            UniqueForSite(queryset=CharacterVariant.objects.all()),
            SameSite(queryset=CharacterVariant.objects.all()),
        ],
    )

    related_entries = PrimaryKeyRelatedField(
        write_only=True,
        queryset=DictionaryEntry.objects.all(),
        allow_null=True,
        many=True,
        validators=[SameSite(queryset=DictionaryEntry.objects.all())],
    )

    def to_representation(self, instance):
        data = CharacterDetailSerializer(instance=instance, context=self.context).data
        return data
