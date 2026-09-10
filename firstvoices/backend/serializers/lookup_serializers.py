from rest_framework import serializers

from backend.models import Audio, Document, Image, Song, Story, Video
from backend.models.dictionary import DictionaryEntry
from backend.search.constants import (
    TYPE_AUDIO,
    TYPE_DOCUMENT,
    TYPE_IMAGE,
    TYPE_SONG,
    TYPE_STORY,
    TYPE_VIDEO,
)
from backend.serializers.base_serializers import (
    BaseSiteContentSerializer,
    ExternalSiteContentUrlMixin,
    LinkedSiteSerializer,
)


class LookupSerializer(ExternalSiteContentUrlMixin, BaseSiteContentSerializer):
    """
    Base serializer for UUID lookup results. Returns identifying information about an
    object and a link to its dtail view, without the site slug in the req context.
    """

    type = serializers.SerializerMethodField(read_only=True)
    site = LinkedSiteSerializer(read_only=True)

    class Meta(BaseSiteContentSerializer.Meta):
        fields = BaseSiteContentSerializer.Meta.fields + ("type",)

    @staticmethod
    def get_type(obj):
        raise NotImplementedError()


class AudioLookupSerializer(LookupSerializer):
    class Meta(LookupSerializer.Meta):
        model = Audio

    @staticmethod
    def get_type(obj):
        return TYPE_AUDIO


class DocumentLookupSerializer(LookupSerializer):
    class Meta(LookupSerializer.Meta):
        model = Document

    @staticmethod
    def get_type(obj):
        return TYPE_DOCUMENT


class ImageLookupSerializer(LookupSerializer):
    class Meta(LookupSerializer.Meta):
        model = Image

    @staticmethod
    def get_type(obj):
        return TYPE_IMAGE


class SongLookupSerializer(LookupSerializer):
    class Meta(LookupSerializer.Meta):
        model = Song

    @staticmethod
    def get_type(obj):
        return TYPE_SONG


class StoryLookupSerializer(LookupSerializer):
    class Meta(LookupSerializer.Meta):
        model = Story

    @staticmethod
    def get_type(obj):
        return TYPE_STORY


class VideoLookupSerializer(LookupSerializer):
    class Meta(LookupSerializer.Meta):
        model = Video

    @staticmethod
    def get_type(obj):
        return TYPE_VIDEO


class DictionaryEntryLookupSerializer(LookupSerializer):
    class Meta(LookupSerializer.Meta):
        model = DictionaryEntry

    @staticmethod
    def get_type(obj):
        # dictionary entires report their own type: "word" or "phrase"
        return obj.type
