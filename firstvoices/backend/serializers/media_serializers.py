from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from backend.models import media

from .base_serializers import (
    CreateSiteContentSerializerMixin,
    ExternalSiteContentUrlMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
    base_id_fields,
)
from .validators import SameSite


class PersonSerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
):
    class Meta:
        model = media.Person
        fields = (
            "id",
            "url",
            "name",
            "bio",
        )


class MediaFileSerializer(serializers.ModelSerializer):
    path = serializers.FileField(source="content")

    class Meta:
        model = media.File
        fields = ("path", "mimetype")


class MediaVideoFileSerializer(MediaFileSerializer):
    class Meta(MediaFileSerializer.Meta):
        model = media.VideoFile
        fields = MediaFileSerializer.Meta.fields + ("height", "width")


class MediaImageFileSerializer(MediaVideoFileSerializer):
    path = serializers.ImageField(source="content")

    class Meta(MediaVideoFileSerializer.Meta):
        model = media.ImageFile


class MediaSerializer(ExternalSiteContentUrlMixin, serializers.ModelSerializer):
    class Meta:
        fields = base_id_fields + (
            "description",
            "acknowledgement",
            "exclude_from_games",
            "exclude_from_kids",
            "is_shared",
            "original",
        )


class AudioSerializer(MediaSerializer):
    """Serializer for Audio objects. Supports audio objects shared between different sites."""

    speakers = PersonSerializer(many=True)
    original = MediaFileSerializer()

    class Meta(MediaSerializer.Meta):
        model = media.Audio
        fields = MediaSerializer.Meta.fields + ("speakers",)


class MediaWithThumbnailsSerializer(MediaSerializer):
    thumbnail = MediaImageFileSerializer()
    small = MediaImageFileSerializer()
    medium = MediaImageFileSerializer()

    class Meta(MediaSerializer.Meta):
        fields = MediaSerializer.Meta.fields + ("thumbnail", "small", "medium")


class ImageSerializer(MediaWithThumbnailsSerializer):
    """Serializer for Audio objects. Supports image objects shared between different sites."""

    original = MediaImageFileSerializer()

    class Meta(MediaWithThumbnailsSerializer.Meta):
        model = media.Image


class VideoSerializer(MediaWithThumbnailsSerializer):
    """Serializer for Audio objects. Supports video objects shared between different sites."""

    original = MediaVideoFileSerializer()

    class Meta(MediaWithThumbnailsSerializer.Meta):
        model = media.Video


class RelatedMediaSerializerMixin(metaclass=serializers.SerializerMetaclass):
    """Mixin that provides standard related media fields"""

    related_audio = AudioSerializer(many=True)
    related_images = ImageSerializer(many=True)
    related_videos = VideoSerializer(many=True)

    class Meta:
        fields = ("related_audio", "related_images", "related_videos")


class RelatedMediaUpdateSerializerMixin(RelatedMediaSerializerMixin):
    related_images = PrimaryKeyRelatedField(
        queryset=media.Image.objects.all(),
        many=True,
        validators=[SameSite(queryset=media.Image.objects.all())],
    )
    related_videos = PrimaryKeyRelatedField(
        queryset=media.Video.objects.all(),
        many=True,
        validators=[SameSite(queryset=media.Video.objects.all())],
    )
    related_audio = PrimaryKeyRelatedField(
        queryset=media.Audio.objects.all(),
        many=True,
        validators=[SameSite(queryset=media.Audio.objects.all())],
    )
