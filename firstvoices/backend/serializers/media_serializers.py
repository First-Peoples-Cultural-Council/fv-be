from rest_framework import serializers

from backend.models import media

from .base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    SiteContentUrlMixin,
    UpdateSerializerMixin,
)


class PersonSerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    SiteContentUrlMixin,
    serializers.ModelSerializer,
):
    class Meta:
        model = media.Person
        fields = ("url", "id", "name", "bio")


class MediaSerializer(SiteContentLinkedTitleSerializer):
    """
    Stub serializer that produces id-title objects.
    """

    content = serializers.FileField(source="original.content")

    class Meta:
        fields = SiteContentLinkedTitleSerializer.Meta.fields + ("content",)


class AudioSerializer(MediaSerializer):
    speakers = PersonSerializer(many=True)

    class Meta(MediaSerializer.Meta):
        model = media.Audio
        fields = MediaSerializer.Meta.fields + ("speakers",)


class ImageSerializer(MediaSerializer):
    content = serializers.ImageField(source="original.content")

    class Meta(MediaSerializer.Meta):
        model = media.Image
        fields = MediaSerializer.Meta.fields


class VideoSerializer(MediaSerializer):
    class Meta(MediaSerializer.Meta):
        model = media.Video


class RelatedMediaSerializerMixin(metaclass=serializers.SerializerMetaclass):
    related_audio = AudioSerializer(many=True)
    related_images = ImageSerializer(many=True)
    related_videos = VideoSerializer(many=True)

    class Meta:
        fields = ("related_audio", "related_images", "related_videos")
