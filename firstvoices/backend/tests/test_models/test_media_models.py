import io
import logging
from unittest.mock import patch

import factory
import pytest
from django.core.files.base import ContentFile
from django.db import NotSupportedError
from embed_video.backends import (
    UnknownBackendException,
    VimeoBackend,
    YoutubeBackend,
    detect_backend,
)
from embed_video.fields import EmbedVideoField
from PIL import Image as PILImage

from backend.models.media import (
    File,
    Image,
    ImageFile,
    Video,
    VideoFile,
    get_output_dimensions,
)
from backend.tests import factories
from backend.tests.factories.media_factories import get_video_content
from backend.tests.test_apis.base.base_media_test import (
    VIMEO_VIDEO_LINK,
    YOUTUBE_VIDEO_LINK,
)

logger = logging.getLogger(__name__)


class TestFileModels:
    file_model_factories = [factories.FileFactory, factories.ImageFileFactory]

    @pytest.mark.parametrize("media_factory", file_model_factories)
    @pytest.mark.django_db
    def test_upload_folder(self, media_factory):
        site = factories.SiteFactory.create()
        instance = media_factory.create(site=site)
        file_field = instance.content
        assert file_field.file
        assert f"/{site.slug}/" in file_field.path

    @pytest.mark.django_db
    def test_file_generated_properties(self):
        site = factories.SiteFactory.create()
        instance = factories.FileFactory.create(site=site)
        assert instance.mimetype == "application/x-empty"

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_imagefile_generated_properties(self):
        site = factories.SiteFactory.create()
        instance = factories.ImageFileFactory.create(
            site=site, content=factory.django.ImageField()
        )
        assert instance.mimetype == "image/jpeg"
        assert instance.height == 100
        assert instance.width == 100

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_videofile_generated_properties(self):
        site = factories.SiteFactory.create()
        instance = factories.VideoFileFactory.create(site=site)
        assert instance.mimetype == "video/mp4"
        assert instance.height == 46
        assert instance.width == 80

    @pytest.mark.parametrize("media_factory", file_model_factories)
    @pytest.mark.django_db
    def test_file_deleted(self, media_factory):
        media_instance = media_factory.create()
        file_field = media_instance.content
        assert file_field.file

        media_instance.delete()

        with pytest.raises(ValueError):
            file_field.file

    @pytest.mark.django_db
    def test_update_file_content_not_supported(self):
        file = factories.VideoFileFactory.create()
        try:
            new_content = get_video_content("small")
            file.content = new_content
            file.save()
            assert False
        except NotSupportedError:
            assert True


class TestAudioModel:
    @pytest.mark.django_db
    def test_related_file_removed_on_delete(self):
        media_instance = factories.AudioFactory.create()
        related_id = media_instance.original.id
        assert File.objects.filter(pk=related_id).count() == 1

        media_instance.delete()

        assert File.objects.filter(pk=related_id).count() == 0

    @pytest.mark.django_db
    def test_related_file_removed_on_update(self):
        media_instance = factories.AudioFactory.create()
        related_id = media_instance.original.id
        assert File.objects.filter(pk=related_id).count() == 1

        media_instance.original = factories.FileFactory.create()
        media_instance.save()

        assert File.objects.filter(pk=related_id).count() == 0


class TestDocumentModel:
    @pytest.mark.django_db
    def test_related_file_removed_on_delete(self):
        media_instance = factories.DocumentFactory.create()
        related_id = media_instance.original.id
        assert File.objects.filter(pk=related_id).count() == 1

        media_instance.delete()

        assert File.objects.filter(pk=related_id).count() == 0

    @pytest.mark.django_db
    def test_related_file_removed_on_update(self):
        media_instance = factories.DocumentFactory.create()
        related_id = media_instance.original.id
        assert File.objects.filter(pk=related_id).count() == 1

        media_instance.original = factories.FileFactory.create()
        media_instance.save()

        assert File.objects.filter(pk=related_id).count() == 0


class TestThumbnailDimensions:
    original_dimensions = {
        "large-landscape": (1500, 1020),
        "large-portrait": (1020, 1500),
        "large-square": (1500, 1500),
        "large-portrait-extreme": (
            1500,
            99,
        ),  # all "extreme" shapes have one dimension smaller than the thumbnail size
        "large-landscape-extreme": (99, 1500),
        "medium-landscape": (999, 600),
        "medium-portrait": (600, 999),
        "medium-landscape-extreme": (999, 99),
        "medium-portrait-extreme": (99, 999),
        "medium-square": (999, 999),
        "small-landscape": (559, 150),
        "small-portrait": (150, 559),
        "small-landscape-extreme": (559, 99),
        "small-portrait-extreme": (99, 559),
        "small-square": (559, 559),
        "thumbnail-portrait": (50, 99),
        "thumbnail-landscape": (99, 50),
        "thumbnail-portrait-extreme": (1, 99),
        "thumbnail-landscape-extreme": (99, 1),
        "thumbnail-square": (99, 99),
    }

    image_sizes = None

    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        self.image_sizes = settings.IMAGE_SIZES

    @pytest.mark.parametrize("original_size", ["thumbnail", "small", "medium", "large"])
    @pytest.mark.parametrize(
        "original_shape",
        ["portrait", "landscape", "portrait-extreme", "landscape-extreme", "square"],
    )
    @pytest.mark.parametrize("max_size_name", ["thumbnail", "small", "medium"])
    def test_thumbnails_never_bigger_than_original(
        self, original_size, original_shape, max_size_name
    ):
        max_size = self.image_sizes[max_size_name]
        original_dimensions = self.original_dimensions[
            f"{original_size}-{original_shape}"
        ]
        result = get_output_dimensions(max_size, *original_dimensions)

        assert result[0] <= original_dimensions[0]
        assert result[1] <= original_dimensions[1]

    @pytest.mark.parametrize("original_size", ["thumbnail", "small", "medium", "large"])
    @pytest.mark.parametrize(
        "original_shape",
        ["portrait", "landscape", "portrait-extreme", "landscape-extreme", "square"],
    )
    @pytest.mark.parametrize("max_size_name", ["thumbnail", "small", "medium"])
    def test_thumbnails_never_bigger_than_size_settings(
        self, original_size, original_shape, max_size_name
    ):
        max_size = self.image_sizes[max_size_name]
        original_dimensions = self.original_dimensions[
            f"{original_size}-{original_shape}"
        ]
        result = get_output_dimensions(max_size, *original_dimensions)

        assert result[0] <= max_size
        assert result[1] <= max_size

    @pytest.mark.parametrize(
        "original_shape",
        ["portrait", "landscape", "portrait-extreme", "landscape-extreme", "square"],
    )
    def test_thumbnails_as_big_as_possible(self, original_shape):
        original_dimensions = self.original_dimensions[f"large-{original_shape}"]
        size_names = ["thumbnail", "small", "medium"]  # sorted smallest to largest

        for index, size_name in enumerate(size_names):
            if index > 0:
                max_size = self.image_sizes[size_name]

                result = get_output_dimensions(max_size, *original_dimensions)

                smaller_size_name = size_names[index - 1]
                smaller_size_setting = self.image_sizes[smaller_size_name]

                assert (result[0] > smaller_size_setting) | (
                    result[1] > smaller_size_setting
                )

    @pytest.mark.parametrize("original_size", ["thumbnail", "small", "medium", "large"])
    @pytest.mark.parametrize(
        "original_shape",
        ["portrait", "landscape", "portrait-extreme", "landscape-extreme", "square"],
    )
    @pytest.mark.parametrize("max_size_name", ["thumbnail", "small", "medium"])
    def test_thumbnails_always_proportional(
        self, original_size, original_shape, max_size_name
    ):
        max_size = self.image_sizes[max_size_name]
        original_dimensions = self.original_dimensions[
            f"{original_size}-{original_shape}"
        ]
        original_proportion_ratio = original_dimensions[1] / original_dimensions[0]

        result = get_output_dimensions(max_size, *original_dimensions)
        result_proportion_ratio = result[1] / result[0]

        # within 10%
        assert (
            abs(result_proportion_ratio - original_proportion_ratio)
            / original_proportion_ratio
        ) < 0.1


class ThumbnailTestMixin:
    image_sizes = None
    size_names = ["thumbnail", "small", "medium"]
    media_model = None
    model_factory = None
    file_model = None
    file_factory = None

    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        # Runs the thumbnail generation synchronously during testing
        settings.CELERY_TASK_ALWAYS_EAGER = True
        self.image_sizes = settings.IMAGE_SIZES

    def create_media_model(self, **kwargs):
        # create an instance
        factory_instance = self.model_factory.create(**kwargs)

        # retrieve a fresh copy after thumbnail generation task has run
        # (synchronously but still not reflected in the factory return value)
        return self.media_model.objects.get(id=factory_instance.id)

    def create_original_file(self, size="thumbnail"):
        raise NotImplementedError

    def create_site_and_instance(self, size="thumbnail"):
        site = factories.SiteFactory.create()
        file = self.create_original_file(size)
        model = self.create_media_model(site=site, original=file)
        return site, model

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_related_file_removed_on_delete(self):
        media_instance = self.create_media_model()
        related_id = media_instance.original.id
        related_image_ids = [
            media_instance.thumbnail.id,
            media_instance.small.id,
            media_instance.medium.id,
        ]

        assert self.file_model.objects.filter(pk=related_id).count() == 1
        for related_id in related_image_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 1

        media_instance.delete()

        assert self.file_model.objects.filter(pk=related_id).count() == 0
        for related_id in related_image_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 0

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_related_file_removed_on_update(self):
        media_instance = self.create_media_model()
        related_id = media_instance.original.id
        related_image_ids = [
            media_instance.thumbnail.id,
            media_instance.small.id,
            media_instance.medium.id,
        ]
        assert self.file_model.objects.filter(pk=related_id).count() == 1
        for related_id in related_image_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 1

        media_instance.original = self.file_factory.create()
        media_instance.save()

        assert self.file_model.objects.filter(pk=related_id).count() == 0
        for related_id in related_image_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 0

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_thumbnail_paths_correct(self):
        site, media_instance = self.create_site_and_instance()

        for size_name in self.image_sizes:
            generated_image = getattr(media_instance, size_name)
            assert generated_image.content.file
            assert f"{site.slug}/" in generated_image.content.path
            assert f"_{size_name}" in generated_image.content.path


class TestVideoModel(ThumbnailTestMixin):
    media_model = Video
    model_factory = factories.VideoFactory
    file_model = VideoFile
    file_factory = factories.VideoFileFactory

    def create_original_file(self, size="thumbnail"):
        return self.file_factory.create(content=get_video_content(size))

    @pytest.mark.django_db
    def test_ffmpeg_probe_returning_none(self, caplog):
        caplog.set_level(logging.WARNING)
        video = factories.VideoFileFactory.create()
        with patch(
            "backend.models.media.VideoFile.get_video_info"
        ) as mock_get_video_info:
            mock_get_video_info.return_value = None
            video.save(update_file_metadata=True)
            assert (
                f"Failed to get video info for [{video.content.name}]. \n"
                in caplog.text
            )


class TestImageModel(ThumbnailTestMixin):
    media_model = Image
    model_factory = factories.ImageFactory
    file_model = ImageFile
    file_factory = factories.ImageFileFactory

    def create_original_file(self, size="thumbnail"):
        return self.file_factory.create()

    def create_original_file_with_exif_orientation(self):
        # Create an image file with exif orientation data
        img = PILImage.new("RGB", (100, 100), color="red")
        exif = img.getexif()
        exif[0x0112] = 6

        # Save the image to a bytes buffer with EXIF data
        img_bytes = io.BytesIO()
        exif_data = exif.tobytes()
        img.save(img_bytes, "JPEG", exif=exif_data)

        # Create a Django ContentFile
        img_bytes.seek(0)
        content_file = ContentFile(img_bytes.read(), "test_image_with_exif.jpg")

        return self.file_factory.create(content=content_file)

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_thumbnails_remove_exif_orientation(self):
        site = factories.SiteFactory.create()
        original_file = self.create_original_file_with_exif_orientation()
        original_file_exif = PILImage.open(original_file.content).getexif()
        assert original_file_exif.get(0x0112) == 6

        image_instance = self.create_media_model(site=site, original=original_file)
        original_id = image_instance.original.id
        thumbnail_image_ids = [
            image_instance.thumbnail.id,
            image_instance.small.id,
            image_instance.medium.id,
        ]

        assert ImageFile.objects.filter(pk=original_id).count() == 1
        for thumbnail_id in thumbnail_image_ids:
            thumbnail_image_content = ImageFile.objects.get(pk=thumbnail_id).content
            thumbnail_image_exif = PILImage.open(thumbnail_image_content).getexif()
            assert thumbnail_image_exif.get(0x0112) is None


class RelatedVideoLinksValidationMixin:
    """
    A mixin to test the validation of related video links.
    """

    def create_instance_with_related_video_links(self, site, related_video_links):
        raise NotImplementedError

    @pytest.mark.parametrize(
        "url",
        ["", "not valid", "https://www.invalid-url.com/", "https://soundcloud.com/"],
    )
    @pytest.mark.django_db
    def test_related_video_links_invalid_base_site(self, url):
        site = factories.SiteFactory.create()
        try:
            related_video_links = [EmbedVideoField(url)]
            instance = self.create_instance_with_related_video_links(
                site=site, related_video_links=related_video_links
            )
            detect_backend(instance.related_video_links[0].verbose_name)
            assert False
        except UnknownBackendException:
            assert True

    @pytest.mark.parametrize(
        "url, backend_class",
        [
            (YOUTUBE_VIDEO_LINK, YoutubeBackend),
            (VIMEO_VIDEO_LINK, VimeoBackend),
        ],
    )
    @pytest.mark.django_db
    def test_related_video_links_valid_base_site(self, url, backend_class):
        site = factories.SiteFactory.create()
        try:
            related_video_links = [EmbedVideoField(url)]
            instance = self.create_instance_with_related_video_links(
                site=site, related_video_links=related_video_links
            )
            backend = detect_backend(instance.related_video_links[0].verbose_name)
            assert isinstance(backend, backend_class)
        except UnknownBackendException:
            assert False
