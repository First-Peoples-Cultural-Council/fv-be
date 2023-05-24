from rest_framework import serializers

from backend.models import media


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = media.Person
        fields = ("id", "name", "bio")


class MediaSerializer(serializers.ModelSerializer):
    """
    Stub serializer that produces id-title objects.
    """

    class Meta:
        fields = ("id", "title", "content")


class AudioSerializer(MediaSerializer):
    speakers = PersonSerializer(many=True)

    class Meta(MediaSerializer.Meta):
        model = media.Audio
        fields = MediaSerializer.Meta.fields + ("speakers",)


class ImageSerializer(MediaSerializer):
    class Meta(MediaSerializer.Meta):
        model = media.Image


class VideoSerializer(MediaSerializer):
    class Meta(MediaSerializer.Meta):
        model = media.Video


class RelatedMediaSerializerMixin(metaclass=serializers.SerializerMetaclass):
    related_audio = AudioSerializer(many=True)
    related_images = ImageSerializer(many=True)
    related_videos = VideoSerializer(many=True)

    class Meta:
        fields = ("related_audio", "related_images", "related_videos")
