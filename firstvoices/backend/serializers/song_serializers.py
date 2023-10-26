from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from backend.models import Lyric, Song
from backend.serializers.base_serializers import (
    ArbitraryIdSerializer,
    LinkedSiteMinimalSerializer,
    LinkedSiteSerializer,
    ReadOnlyVisibilityFieldMixin,
    SiteContentLinkedTitleSerializer,
    WritableControlledSiteContentSerializer,
    WritableVisibilityField,
    audience_fields,
    base_id_fields,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import (
    RelatedImageMinimalSerializer,
    RelatedMediaSerializerMixin,
    RelatedVideoMinimalSerializer,
)


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
    visibility = WritableVisibilityField(required=True)

    title_translation = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    introduction = serializers.CharField(required=False, allow_blank=True, default="")
    introduction_translation = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    lyrics = LyricSerializer(many=True)

    notes = serializers.ListField(child=ArbitraryIdSerializer(), required=False)
    acknowledgements = serializers.ListField(
        child=ArbitraryIdSerializer(), required=False
    )

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


class SongListSerializer(
    ReadOnlyVisibilityFieldMixin, SiteContentLinkedTitleSerializer
):
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


class SongMinimalSerializer(ModelSerializer):
    site = LinkedSiteMinimalSerializer(read_only=True)
    related_images = RelatedImageMinimalSerializer(
        many=True, required=False, read_only=True
    )
    related_videos = RelatedVideoMinimalSerializer(
        many=True, required=False, read_only=True
    )

    class Meta:
        model = Song
        fields = (
            "id",
            "title",
            "title_translation",
            "hide_overlay",
            "site",
            "related_images",
            "related_videos",
        )
        read_only_fields = ("id", "title", "title_translation", "hide_overlay")
