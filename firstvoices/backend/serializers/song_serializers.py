from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from backend.models import Lyric, Song
from backend.models.media import Image
from backend.serializers.base_serializers import (
    CreateControlledSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
    WritableVisibilityField,
    base_id_fields,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import (
    ImageSerializer,
    RelatedMediaSerializerMixin,
    WriteableRelatedImageSerializer,
)
from backend.serializers.site_serializers import LinkedSiteSerializer


class LyricSerializer(ModelSerializer):
    class Meta:
        model = Lyric
        fields = ("id", "text", "translation")
        read_only_fields = ("id",)


class SongSerializer(
    CreateControlledSiteContentSerializerMixin,
    RelatedMediaSerializerMixin,
    UpdateSerializerMixin,
    SiteContentLinkedTitleSerializer,
):
    cover_image = WriteableRelatedImageSerializer(
        allow_null=True, queryset=Image.objects.all()
    )
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
        Lyric.objects.filter(song__id=instance.id).delete()
        try:
            lyrics = validated_data.pop("lyrics")
            for index, lyric_data in enumerate(lyrics):
                Lyric.objects.create(song=instance, ordering=index, **lyric_data)
        except KeyError:
            pass

        return super().update(instance, validated_data)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
        read_only_fields = (
            base_id_fields,
            base_timestamp_fields,
            "site",
        )
        fields = (
            base_timestamp_fields
            + RelatedMediaSerializerMixin.Meta.fields
            + (
                "url",
                "id",
                "hide_overlay",
                "site",
                "cover_image",
                "visibility",
                "title",
                "title_translation",
                "introduction",
                "introduction_translation",
                "notes",
                "lyrics",
                "acknowledgements",
                "exclude_from_games",
                "exclude_from_kids",
            )
        )


class SongListSerializer(SiteContentLinkedTitleSerializer):
    cover_image = ImageSerializer()
    visibility = serializers.CharField(read_only=True, source="get_visibility_display")

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "title_translation",
            "visibility",
            "cover_image",
            "hide_overlay",
            "exclude_from_games",
            "exclude_from_kids",
        )
