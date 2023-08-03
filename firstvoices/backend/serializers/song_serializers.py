from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from backend.models import Lyric, Song
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    WritableControlledSiteContentSerializer,
    WritableVisibilityField,
    audience_fields,
    base_id_fields,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import RelatedMediaSerializerMixin
from backend.serializers.site_serializers import LinkedSiteSerializer


class LyricSerializer(ModelSerializer):
    class Meta:
        model = Lyric
        fields = ("id", "text", "translation")
        read_only_fields = ("id",)


class SongSerializer(
    RelatedMediaSerializerMixin,
    WritableControlledSiteContentSerializer,
):
    site = LinkedSiteSerializer(required=False, read_only=True)
    lyrics = LyricSerializer(many=True)
    visibility = WritableVisibilityField(required=True)

    def create(self, validated_data):
        lyrics = validated_data.pop("lyrics")

        created = super().create(validated_data)

        for index, lyric_data in enumerate(lyrics):
            Lyric.objects.create(song=created, ordering=index, **lyric_data)

        return created

    def update(self, instance, validated_data):
        if "lyrics" in validated_data:
            Lyric.objects.filter(song__id=instance.id).delete()
            lyrics = validated_data.pop("lyrics")
            for index, lyric_data in enumerate(lyrics):
                Lyric.objects.create(song=instance, ordering=index, **lyric_data)

        return super().update(instance, validated_data)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
        read_only_fields = (
            base_id_fields,
            base_timestamp_fields,
            "site",
        )
        fields = (
            WritableControlledSiteContentSerializer.Meta.fields
            + (
                "hide_overlay",
                "site",
                "visibility",
                "title",
                "title_translation",
                "introduction",
                "introduction_translation",
                "notes",
                "lyrics",
                "acknowledgements",
            )
            + audience_fields
            + RelatedMediaSerializerMixin.Meta.fields
        )


class SongListSerializer(SiteContentLinkedTitleSerializer):
    visibility = serializers.CharField(read_only=True, source="get_visibility_display")

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
        fields = (
            SiteContentLinkedTitleSerializer.Meta.fields
            + audience_fields
            + (
                "visibility",
                "title_translation",
                "hide_overlay",
            )
        )
