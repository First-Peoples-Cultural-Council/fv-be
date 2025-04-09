from rest_framework import serializers

from backend.models import (
    Audio,
    Document,
    Image,
    Person,
    Song,
    Story,
    Video,
    dictionary,
)
from backend.serializers.base_serializers import (
    LinkedSiteMinimalSerializer,
    ReadOnlyVisibilityFieldMixin,
)
from backend.serializers.fields import TextListField
from backend.serializers.files_serializers import FileSerializer
from backend.serializers.media_serializers import (
    ImageFileSerializer,
    ImageUploadSerializer,
    VideoUploadSerializer,
)


class PersonMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ("id", "name", "bio")


class MediaMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "created",
            "last_modified",
            "original",
            "title",
            "description",
            "acknowledgement",
        )
        read_only_fields = ("id", "original", "title", "description", "acknowledgement")


class AudioMinimalSerializer(MediaMinimalSerializer):
    original = FileSerializer(read_only=True)
    speakers = PersonMinimalSerializer(many=True, read_only=True)

    class Meta(MediaMinimalSerializer.Meta):
        model = Audio
        fields = MediaMinimalSerializer.Meta.fields + ("speakers",)


class RelatedImageMinimalSerializer(serializers.ModelSerializer):
    original = ImageUploadSerializer(read_only=True)

    class Meta:
        model = Image
        fields = ("id", "original")
        read_only_fields = ("id", "original")


class RelatedVideoMinimalSerializer(RelatedImageMinimalSerializer):
    original = VideoUploadSerializer(read_only=True)

    class Meta(RelatedImageMinimalSerializer.Meta):
        model = Video


class DocumentMinimalSerializer(MediaMinimalSerializer):
    original = FileSerializer(read_only=True)

    class Meta(MediaMinimalSerializer.Meta):
        model = Document


class ImageMinimalSerializer(MediaMinimalSerializer):
    original = ImageUploadSerializer(read_only=True)
    small = ImageFileSerializer(read_only=True)

    class Meta(MediaMinimalSerializer.Meta):
        model = Image
        fields = MediaMinimalSerializer.Meta.fields + ("small",)
        read_only_fields = MediaMinimalSerializer.Meta.read_only_fields + ("small",)


class VideoMinimalSerializer(ImageMinimalSerializer):
    original = VideoUploadSerializer(read_only=True)

    class Meta(ImageMinimalSerializer.Meta):
        model = Video


class DictionaryEntryMinimalSerializer(
    ReadOnlyVisibilityFieldMixin, serializers.ModelSerializer
):
    site = LinkedSiteMinimalSerializer(read_only=True)
    translations = TextListField(required=False, allow_empty=True)
    related_audio = AudioMinimalSerializer(many=True, required=False, read_only=True)
    related_images = RelatedImageMinimalSerializer(
        many=True, required=False, read_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove the split_chars_base field from the serializer if the games_flag is not set to True
        if not self.context.get("games_flag"):
            self.fields.pop("split_chars_base")

    class Meta:
        model = dictionary.DictionaryEntry
        fields = (
            "id",
            "created",
            "last_modified",
            "visibility",
            "title",
            "type",
            "site",
            "translations",
            "related_audio",
            "related_images",
            "split_chars_base",
        )
        read_only_fields = ("id", "title", "type")


class SongMinimalSerializer(ReadOnlyVisibilityFieldMixin, serializers.ModelSerializer):
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
            "created",
            "last_modified",
            "visibility",
            "title",
            "title_translation",
            "hide_overlay",
            "site",
            "related_images",
            "related_videos",
        )
        read_only_fields = ("id", "title", "title_translation", "hide_overlay")


class StoryMinimalSerializer(ReadOnlyVisibilityFieldMixin, serializers.ModelSerializer):
    site = LinkedSiteMinimalSerializer(read_only=True)
    related_images = RelatedImageMinimalSerializer(
        many=True, required=False, read_only=True
    )
    related_videos = RelatedVideoMinimalSerializer(
        many=True, required=False, read_only=True
    )

    class Meta:
        model = Story
        fields = (
            "id",
            "created",
            "last_modified",
            "visibility",
            "title",
            "title_translation",
            "author",
            "hide_overlay",
            "site",
            "related_images",
            "related_videos",
        )


class SearchResultSerializer(serializers.Serializer):
    type = serializers.SerializerMethodField(
        read_only=True
    )  # value here needs to be set per-type
    search_result_id = serializers.CharField(
        read_only=True
    )  # always the search result id
    entry_serializer = None
    entry = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_type(obj):
        raise NotImplementedError()

    def get_entry(self, obj):
        serializer = self.entry_serializer(obj["entry"], context=self.context)
        return serializer.data


class AudioSearchResultSerializer(SearchResultSerializer):
    entry_serializer = AudioMinimalSerializer

    @staticmethod
    def get_type(obj):
        return "audio"


class DocumentSearchResultSerializer(SearchResultSerializer):
    entry_serializer = DocumentMinimalSerializer

    @staticmethod
    def get_type(obj):
        return "document"


class ImageSearchResultSerializer(SearchResultSerializer):
    entry_serializer = ImageMinimalSerializer

    @staticmethod
    def get_type(obj):
        return "image"


class VideoSearchResultSerializer(SearchResultSerializer):
    entry_serializer = VideoMinimalSerializer

    @staticmethod
    def get_type(obj):
        return "video"


class DictionaryEntrySearchResultSerializer(SearchResultSerializer):
    entry_serializer = DictionaryEntryMinimalSerializer

    @staticmethod
    def get_type(obj):
        return obj["entry"].type


class SongSearchResultSerializer(SearchResultSerializer):
    entry_serializer = SongMinimalSerializer

    @staticmethod
    def get_type(obj):
        return "song"


class StorySearchResultSerializer(SearchResultSerializer):
    entry_serializer = StoryMinimalSerializer

    @staticmethod
    def get_type(obj):
        return "story"
