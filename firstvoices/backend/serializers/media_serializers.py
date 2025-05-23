import functools

from drf_spectacular.utils import extend_schema_field
from embed_video.backends import (
    UnknownBackendException,
    VideoDoesntExistException,
    detect_backend,
)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from backend.models.files import File
from backend.models.media import (
    SUPPORTED_FILETYPES,
    Audio,
    Document,
    Image,
    ImageFile,
    Person,
    Video,
    VideoFile,
)
from backend.models.validators import validate_no_duplicate_urls
from backend.serializers.utils.context_utils import get_site_from_context

from .base_serializers import (
    CreateSiteContentSerializerMixin,
    ExternalSiteContentUrlMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
    ValidateNonNullableCharFieldsMixin,
    base_id_fields,
)
from .files_serializers import FileSerializer, FileUploadSerializer
from .validators import SupportedFileType


class PersonSerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    ValidateNonNullableCharFieldsMixin,
    SiteContentLinkedTitleSerializer,
):
    bio = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )

    class Meta:
        model = Person
        fields = (
            "id",
            "url",
            "name",
            "bio",
        )


class WriteableRelatedPersonSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return PersonSerializer(context=self.context).to_representation(value)


class VideoFileSerializer(FileSerializer):
    class Meta(FileSerializer.Meta):
        model = VideoFile
        fields = FileSerializer.Meta.fields + ("height", "width")


class ImageFileSerializer(VideoFileSerializer):
    path = serializers.ImageField(source="content")

    class Meta(VideoFileSerializer.Meta):
        model = ImageFile


class ImageUploadSerializer(serializers.ImageField):
    def to_representation(self, value):
        return ImageFileSerializer(context=self.context).to_representation(value)


class VideoUploadSerializer(serializers.FileField):
    def to_representation(self, value):
        return VideoFileSerializer(context=self.context).to_representation(value)


class MediaSerializer(ExternalSiteContentUrlMixin, serializers.ModelSerializer):
    # fw-4650 should find a better way to camel-case these
    excludeFromKids = serializers.BooleanField(
        source="exclude_from_kids", default=False
    )
    excludeFromGames = serializers.BooleanField(
        source="exclude_from_games", default=False
    )

    def create_file(self, validated_data, filetype):
        file_data = validated_data.pop("original")
        user = self.context["request"].user
        site = get_site_from_context(self)
        file = filetype(
            content=file_data,
            site=site,
            created_by=user,
            last_modified_by=user,
        )
        file.save()
        return file

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        request = self.context.get("request", None)
        if request and getattr(request, "method", None) in ["PUT", "PATCH"]:
            fields["original"].read_only = True
        return fields

    class Meta:
        fields = base_id_fields + (
            "description",
            "acknowledgement",
            "excludeFromKids",
            "excludeFromGames",
            "original",
        )


class AudioSerializer(
    UpdateSerializerMixin, CreateSiteContentSerializerMixin, MediaSerializer
):
    """Serializer for Audio objects. Supports audio objects shared between different sites."""

    speakers = WriteableRelatedPersonSerializer(
        many=True,
        queryset=Person.objects.all(),
        style={
            "base_template": "input.html"
        },  # for local dev, settings for browseable api
    )
    original = FileUploadSerializer(
        validators=[SupportedFileType(mimetypes=SUPPORTED_FILETYPES["audio"])],
    )

    class Meta(MediaSerializer.Meta):
        model = Audio
        fields = MediaSerializer.Meta.fields + ("speakers",)

    def create(self, validated_data):
        validated_data["original"] = self.create_file(validated_data, File)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "original" in validated_data:
            validated_data["original"] = self.create_file(validated_data, File)

        return super().update(instance, validated_data)


class DocumentSerializer(
    UpdateSerializerMixin, CreateSiteContentSerializerMixin, MediaSerializer
):
    """Serializer for Document objects. Supports document objects shared between different sites."""

    original = FileUploadSerializer(
        validators=[SupportedFileType(mimetypes=SUPPORTED_FILETYPES["document"])],
    )

    class Meta(MediaSerializer.Meta):
        model = Document
        fields = MediaSerializer.Meta.fields

    def create(self, validated_data):
        validated_data["original"] = self.create_file(validated_data, File)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "original" in validated_data:
            validated_data["original"] = self.create_file(validated_data, File)

        return super().update(instance, validated_data)


class MediaWithThumbnailsSerializer(MediaSerializer):
    thumbnail = ImageFileSerializer(read_only=True)
    small = ImageFileSerializer(read_only=True)
    medium = ImageFileSerializer(read_only=True)

    class Meta(MediaSerializer.Meta):
        fields = MediaSerializer.Meta.fields + ("thumbnail", "small", "medium")


class ImageSerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    MediaWithThumbnailsSerializer,
):
    """Serializer for Image objects. Supports image objects shared between different sites."""

    original = ImageUploadSerializer(
        validators=[SupportedFileType(mimetypes=SUPPORTED_FILETYPES["image"])],
    )

    def create(self, validated_data):
        validated_data["original"] = self.create_file(validated_data, ImageFile)
        created = super().create(validated_data)
        return created

    def update(self, instance, validated_data):
        if "original" in validated_data:
            validated_data["original"] = self.create_file(validated_data, ImageFile)

        return super().update(instance, validated_data)

    class Meta(MediaWithThumbnailsSerializer.Meta):
        model = Image


class VideoSerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    MediaWithThumbnailsSerializer,
):
    """Serializer for Video objects. Supports video objects shared between different sites."""

    original = VideoUploadSerializer(
        validators=[SupportedFileType(mimetypes=SUPPORTED_FILETYPES["video"])],
    )

    class Meta(MediaWithThumbnailsSerializer.Meta):
        model = Video

    def create(self, validated_data):
        validated_data["original"] = self.create_file(validated_data, VideoFile)
        created = super().create(validated_data)
        return created

    def update(self, instance, validated_data):
        if "original" in validated_data:
            validated_data["original"] = self.create_file(validated_data, VideoFile)

        return super().update(instance, validated_data)


class WriteableRelatedAudioSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return AudioSerializer(context=self.context).to_representation(value)


class WriteableRelatedDocumentSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return DocumentSerializer(context=self.context).to_representation(value)


class WriteableRelatedVideoSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return VideoSerializer(context=self.context).to_representation(value)


class WriteableRelatedImageSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return ImageSerializer(context=self.context).to_representation(value)


class RelatedVideoLinksSerializer(serializers.Serializer):
    video_link = serializers.SerializerMethodField()
    embed_link = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    @staticmethod
    @functools.cache
    def get_video_link(obj):
        return obj

    @staticmethod
    @functools.cache
    def get_embed_link(obj):
        backend = detect_backend(obj)
        return backend.get_url()

    @staticmethod
    @functools.cache
    def get_thumbnail(obj):
        backend = detect_backend(obj)
        return backend.get_thumbnail_url()

    class Meta:
        fields = ("video_link", "embed_link", "thumbnail")


class RelatedMediaSerializerMixin(metaclass=serializers.SerializerMetaclass):
    """Mixin that provides standard related media fields"""

    related_audio = WriteableRelatedAudioSerializer(
        required=False,
        many=True,
        queryset=Audio.objects.all(),
        validators=[UniqueValidator(queryset=Audio.objects.all())],
    )
    related_documents = WriteableRelatedDocumentSerializer(
        required=False,
        many=True,
        queryset=Document.objects.all(),
        validators=[UniqueValidator(queryset=Document.objects.all())],
    )
    related_images = WriteableRelatedImageSerializer(
        required=False,
        many=True,
        queryset=Image.objects.all(),
        validators=[UniqueValidator(queryset=Image.objects.all())],
    )
    related_videos = WriteableRelatedVideoSerializer(
        required=False,
        many=True,
        queryset=Video.objects.all(),
        validators=[UniqueValidator(queryset=Video.objects.all())],
    )
    related_video_links = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        if (
            "related_video_links" in self.context.get("request").data
            and self.context.get("request").data["related_video_links"] == []
        ):
            instance.related_video_links = []

        return super().update(instance, validated_data)

    @extend_schema_field(
        field={
            "type": "array",
            "items": {"type": "string"},
            "example": [
                {
                    "videoLink": "https://www.youtube.com/watch?v=abcdefghijk",
                    "embedLink": "https://www.youtube.com/embed/abcdefghijk",
                    "thumbnail": "https://img.youtube.com/vi/abcdefghijk/hqdefault.jpg",
                }
            ],
        }
    )
    def get_related_video_links(self, instance):
        if self.context.get("request").method in ["GET"]:
            return RelatedVideoLinksSerializer(
                instance.related_video_links, many=True
            ).data
        else:
            return instance.related_video_links

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["related_video_links"] = RelatedVideoLinksSerializer(
            instance.related_video_links, many=True
        ).data
        return representation

    def validate(self, attrs):
        related_video_links = self.context.get("request").data.get(
            "related_video_links"
        )
        if related_video_links:
            validate_no_duplicate_urls(related_video_links)
            for link in related_video_links:
                try:
                    backend = detect_backend(link)
                    backend.get_url()
                    backend.get_thumbnail_url()
                except UnknownBackendException:
                    raise serializers.ValidationError(
                        f"The related video link {link} is not supported. Please use a YouTube or Vimeo link."
                    )
                except VideoDoesntExistException:
                    raise serializers.ValidationError(
                        f"The related video link {link} is not valid. Please check the link and try again."
                    )

            attrs["related_video_links"] = related_video_links
        return super().validate(attrs)

    class Meta:
        fields = (
            "related_audio",
            "related_documents",
            "related_images",
            "related_videos",
            "related_video_links",
        )
