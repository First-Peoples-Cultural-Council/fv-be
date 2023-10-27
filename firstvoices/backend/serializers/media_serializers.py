from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from backend.models import media

from .base_serializers import (
    CreateSiteContentSerializerMixin,
    ExternalSiteContentUrlMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
    base_id_fields,
)
from .utils import get_site_from_context
from .validators import SupportedFileType


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


class WriteableRelatedPersonSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return PersonSerializer(context=self.context).to_representation(value)


class MediaFileSerializer(serializers.ModelSerializer):
    path = serializers.FileField(source="content")

    class Meta:
        model = media.File
        fields = ("path", "mimetype", "size")


class MediaFileUploadSerializer(serializers.FileField):
    def to_representation(self, value):
        return MediaFileSerializer(context=self.context).to_representation(value)


class MediaVideoFileSerializer(MediaFileSerializer):
    class Meta(MediaFileSerializer.Meta):
        model = media.VideoFile
        fields = MediaFileSerializer.Meta.fields + ("height", "width")


class MediaImageFileSerializer(MediaVideoFileSerializer):
    path = serializers.ImageField(source="content")

    class Meta(MediaVideoFileSerializer.Meta):
        model = media.ImageFile


class ImageUploadSerializer(serializers.ImageField):
    def to_representation(self, value):
        return MediaImageFileSerializer(context=self.context).to_representation(value)


class VideoUploadSerializer(serializers.FileField):
    def to_representation(self, value):
        return MediaVideoFileSerializer(context=self.context).to_representation(value)


class MediaSerializer(ExternalSiteContentUrlMixin, serializers.ModelSerializer):
    # fw-4650 should find a better way to camel-case these
    excludeFromKids = serializers.BooleanField(
        source="exclude_from_kids", default=False
    )
    excludeFromGames = serializers.BooleanField(
        source="exclude_from_games", default=False
    )
    isShared = serializers.BooleanField(source="is_shared", default=False)

    class Meta:
        fields = base_id_fields + (
            "description",
            "acknowledgement",
            "excludeFromKids",
            "excludeFromGames",
            "isShared",
            "original",
        )


class AudioSerializer(CreateSiteContentSerializerMixin, MediaSerializer):
    """Serializer for Audio objects. Supports audio objects shared between different sites."""

    speakers = WriteableRelatedPersonSerializer(
        many=True,
        queryset=media.Person.objects.all(),
        style={
            "base_template": "input.html"
        },  # for local dev, settings for browseable api
    )
    original = MediaFileUploadSerializer(
        validators=[
            SupportedFileType(
                mimetypes=[
                    "audio/wave",
                    "audio/wav",
                    "audio/x-wav",
                    "audio/x-pn-wav",
                    "audio/vnd.wav",
                    "audio/mpeg",
                    "audio/mp3",
                    "audio/mpeg3",
                    "audio/x-mpeg-3",
                    "application/octet-stream",  # fallback for weird mp3 files; see fw-4829
                ]
            )
        ],
    )

    class Meta(MediaSerializer.Meta):
        model = media.Audio
        fields = MediaSerializer.Meta.fields + ("speakers",)

    def create(self, validated_data):
        file_data = validated_data.pop("original")
        user = self.context["request"].user
        site = get_site_from_context(self)
        file = media.File(
            content=file_data,
            site=site,
            created_by=user,
            last_modified_by=user,
        )
        file.save()

        validated_data["original"] = file
        created = super().create(validated_data)
        return created


class MediaWithThumbnailsSerializer(MediaSerializer):
    thumbnail = MediaImageFileSerializer(read_only=True)
    small = MediaImageFileSerializer(read_only=True)
    medium = MediaImageFileSerializer(read_only=True)

    class Meta(MediaSerializer.Meta):
        fields = MediaSerializer.Meta.fields + ("thumbnail", "small", "medium")


class ImageSerializer(
    CreateSiteContentSerializerMixin,
    MediaWithThumbnailsSerializer,
):
    """Serializer for Image objects. Supports image objects shared between different sites."""

    original = ImageUploadSerializer(
        validators=[
            SupportedFileType(
                mimetypes=["image/jpeg", "image/gif", "image/png", "image/tiff"]
            )
        ],
    )

    def create(self, validated_data):
        file_data = validated_data.pop("original")
        user = self.context["request"].user
        site = get_site_from_context(self)
        file = media.ImageFile(
            content=file_data,
            site=site,
            created_by=user,
            last_modified_by=user,
        )
        file.save()

        validated_data["original"] = file
        created = super().create(validated_data)
        return created

    class Meta(MediaWithThumbnailsSerializer.Meta):
        model = media.Image


class VideoSerializer(CreateSiteContentSerializerMixin, MediaWithThumbnailsSerializer):
    """Serializer for Video objects. Supports video objects shared between different sites."""

    original = VideoUploadSerializer(
        validators=[SupportedFileType(mimetypes=["video/mp4", "video/quicktime"])],
    )

    class Meta(MediaWithThumbnailsSerializer.Meta):
        model = media.Video

    def create(self, validated_data):
        file_data = validated_data.pop("original")
        user = self.context["request"].user
        site = get_site_from_context(self)
        file = media.VideoFile(
            content=file_data,
            site=site,
            created_by=user,
            last_modified_by=user,
        )
        file.save()

        validated_data["original"] = file
        created = super().create(validated_data)
        return created


class WriteableRelatedAudioSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return AudioSerializer(context=self.context).to_representation(value)


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


class RelatedMediaSerializerMixin(metaclass=serializers.SerializerMetaclass):
    """Mixin that provides standard related media fields"""

    related_audio = WriteableRelatedAudioSerializer(
        required=False,
        many=True,
        queryset=media.Audio.objects.all(),
        validators=[UniqueValidator(queryset=media.Audio.objects.all())],
    )
    related_images = WriteableRelatedImageSerializer(
        required=False,
        many=True,
        queryset=media.Image.objects.all(),
        validators=[UniqueValidator(queryset=media.Image.objects.all())],
    )
    related_videos = WriteableRelatedVideoSerializer(
        required=False,
        many=True,
        queryset=media.Video.objects.all(),
        validators=[UniqueValidator(queryset=media.Video.objects.all())],
    )

    class Meta:
        fields = ("related_audio", "related_images", "related_videos")


class AudioMinimalSerializer(serializers.ModelSerializer):
    original = MediaFileSerializer(read_only=True)
    speakers = PersonSerializer(many=True, read_only=True)

    class Meta:
        model = media.Audio
        fields = (
            "id",
            "title",
            "description",
            "acknowledgement",
            "speakers",
            "original",
        )
        read_only_fields = ("id", "original")


class RelatedImageMinimalSerializer(serializers.ModelSerializer):
    original = ImageUploadSerializer(read_only=True)

    class Meta:
        model = media.Image
        fields = ("id", "original")
        read_only_fields = ("id", "original")


class RelatedVideoMinimalSerializer(RelatedImageMinimalSerializer):
    original = VideoUploadSerializer(read_only=True)

    class Meta(RelatedImageMinimalSerializer.Meta):
        model = media.Video


class MediaMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "original", "title", "description")
        read_only_fields = ("id", "original", "title", "description")


class ImageMinimalSerializer(MediaMinimalSerializer):
    original = ImageUploadSerializer(read_only=True)
    small = MediaImageFileSerializer(read_only=True)

    class Meta(MediaMinimalSerializer.Meta):
        model = media.Image
        fields = MediaMinimalSerializer.Meta.fields + ("small",)
        read_only_fields = MediaMinimalSerializer.Meta.read_only_fields + ("small",)


class VideoMinimalSerializer(ImageMinimalSerializer):
    original = VideoUploadSerializer(read_only=True)

    class Meta(ImageMinimalSerializer.Meta):
        model = media.Video
