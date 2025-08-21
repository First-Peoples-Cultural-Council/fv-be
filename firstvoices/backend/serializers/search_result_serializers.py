from django.db.models import Prefetch
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
    VideoFileSerializer,
)


class PersonMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ("id", "name", "bio")


class MediaMinimalSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    last_modified_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        fields = (
            "id",
            "created",
            "created_by",
            "last_modified",
            "last_modified_by",
            "original",
            "title",
            "description",
            "acknowledgement",
        )
        read_only_fields = ("id", "original", "title", "description", "acknowledgement")

    @classmethod
    def make_queryset_eager(cls, queryset, user=None):
        """Add prefetching as required by this serializer"""
        return queryset.select_related(
            "original",
            "created_by",
            "last_modified_by",
        )


class AudioMinimalSerializer(MediaMinimalSerializer):
    original = FileSerializer(read_only=True)
    speakers = PersonMinimalSerializer(many=True, read_only=True)

    class Meta(MediaMinimalSerializer.Meta):
        model = Audio
        fields = MediaMinimalSerializer.Meta.fields + ("speakers",)

    @classmethod
    def make_queryset_eager(cls, queryset, user=None):
        """Add prefetching as required by this serializer"""
        queryset = super().make_queryset_eager(queryset)
        return queryset.prefetch_related("speakers")


class RelatedImageMinimalSerializer(serializers.ModelSerializer):
    original = ImageFileSerializer(read_only=True)

    class Meta:
        model = Image
        fields = ("id", "original")
        read_only_fields = ("id", "original")

    @classmethod
    def make_queryset_eager(cls, queryset, user=None):
        """Add prefetching as required by this serializer"""
        return queryset.select_related("original")


class RelatedVideoMinimalSerializer(RelatedImageMinimalSerializer):
    original = VideoFileSerializer(read_only=True)

    class Meta(RelatedImageMinimalSerializer.Meta):
        model = Video


class DocumentMinimalSerializer(MediaMinimalSerializer):
    original = FileSerializer(read_only=True)

    class Meta(MediaMinimalSerializer.Meta):
        model = Document


class ImageMinimalSerializer(MediaMinimalSerializer):
    original = ImageFileSerializer(read_only=True)
    small = ImageFileSerializer(read_only=True)

    class Meta(MediaMinimalSerializer.Meta):
        model = Image
        fields = MediaMinimalSerializer.Meta.fields + ("small",)
        read_only_fields = MediaMinimalSerializer.Meta.read_only_fields + ("small",)

    @classmethod
    def make_queryset_eager(cls, queryset, user=None):
        """Add prefetching as required by this serializer"""
        queryset = super().make_queryset_eager(queryset)
        return queryset.select_related("small")


class VideoMinimalSerializer(ImageMinimalSerializer):
    original = VideoFileSerializer(read_only=True)

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
    created_by = serializers.StringRelatedField(read_only=True)
    last_modified_by = serializers.StringRelatedField(read_only=True)

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
            "created_by",
            "last_modified",
            "last_modified_by",
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

    @classmethod
    def make_queryset_eager(cls, queryset, user):
        """Add prefetching as required by this serializer"""
        return queryset.select_related(
            "site",
            "created_by",
            "last_modified_by",
        ).prefetch_related(
            Prefetch(
                "related_audio",
                queryset=Audio.objects.visible(user)
                .select_related("original")
                .prefetch_related("speakers"),
            ),
            Prefetch(
                "related_images",
                queryset=Image.objects.visible(user).select_related(
                    "original", "small"
                ),
            ),
            Prefetch(
                "related_videos",
                queryset=Video.objects.visible(user).select_related(
                    "original", "small"
                ),
            ),
        )


class SongMinimalSerializer(ReadOnlyVisibilityFieldMixin, serializers.ModelSerializer):
    site = LinkedSiteMinimalSerializer(read_only=True)
    related_images = RelatedImageMinimalSerializer(
        many=True, required=False, read_only=True
    )
    related_videos = RelatedVideoMinimalSerializer(
        many=True, required=False, read_only=True
    )
    created_by = serializers.StringRelatedField(read_only=True)
    last_modified_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Song
        fields = (
            "id",
            "created",
            "created_by",
            "last_modified",
            "last_modified_by",
            "visibility",
            "title",
            "title_translation",
            "hide_overlay",
            "site",
            "related_images",
            "related_videos",
        )
        read_only_fields = ("id", "title", "title_translation", "hide_overlay")

    @classmethod
    def make_queryset_eager(cls, queryset, user):
        """Add prefetching as required by this serializer"""
        return queryset.select_related(
            "site",
            "created_by",
            "last_modified_by",
        ).prefetch_related(
            Prefetch(
                "related_audio",
                queryset=Audio.objects.visible(user)
                .select_related("original")
                .prefetch_related("speakers"),
            ),
            Prefetch(
                "related_images",
                queryset=Image.objects.visible(user).select_related(
                    "original", "small"
                ),
            ),
            Prefetch(
                "related_videos",
                queryset=Video.objects.visible(user).select_related(
                    "original", "small"
                ),
            ),
        )


class StoryMinimalSerializer(ReadOnlyVisibilityFieldMixin, serializers.ModelSerializer):
    site = LinkedSiteMinimalSerializer(read_only=True)
    related_images = RelatedImageMinimalSerializer(
        many=True, required=False, read_only=True
    )
    related_videos = RelatedVideoMinimalSerializer(
        many=True, required=False, read_only=True
    )
    created_by = serializers.StringRelatedField(read_only=True)
    last_modified_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Story
        fields = (
            "id",
            "created",
            "created_by",
            "last_modified",
            "last_modified_by",
            "visibility",
            "title",
            "title_translation",
            "author",
            "hide_overlay",
            "site",
            "related_images",
            "related_videos",
        )

    @classmethod
    def make_queryset_eager(cls, queryset, user):
        """Add prefetching as required by this serializer"""
        return queryset.select_related(
            "site",
            "created_by",
            "last_modified_by",
        ).prefetch_related(
            Prefetch(
                "related_audio",
                queryset=Audio.objects.visible(user)
                .select_related("original")
                .prefetch_related("speakers"),
            ),
            Prefetch(
                "related_images",
                queryset=Image.objects.visible(user).select_related(
                    "original", "small"
                ),
            ),
            Prefetch(
                "related_videos",
                queryset=Video.objects.visible(user).select_related(
                    "original", "small"
                ),
            ),
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

    @classmethod
    def make_queryset_eager(cls, queryset, user):
        """Add prefetching as required by this serializer"""
        return cls.entry_serializer.make_queryset_eager(queryset, user)


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
