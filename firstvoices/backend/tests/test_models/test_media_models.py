import logging
from unittest.mock import patch

import factory
import pytest
from django.db import NotSupportedError
from embed_video.backends import (
    UnknownBackendException,
    VimeoBackend,
    YoutubeBackend,
    detect_backend,
)
from embed_video.fields import EmbedVideoField

from backend.models.media import File, Image, ImageFile, Video, VideoFile
from backend.tests import factories
from backend.tests.factories.media_factories import get_video_content

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
    def test_imagefile_generated_properties(self):
        site = factories.SiteFactory.create()
        instance = factories.ImageFileFactory.create(site=site)
        assert instance.mimetype == "image/jpeg"
        assert instance.height == 100
        assert instance.width == 100

    @pytest.mark.django_db
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


class TestVideoModel:
    image_sizes = None
    size_names = ["thumbnail", "small", "medium"]
    video_dimensions = {
        "large-landscape": (1500, 1020),
        "large-portrait": (1020, 1500),
        "large-square": (1500, 1500),
        "large-portrait-extreme": (1500, 99),
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

    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        # Runs the thumbnail generation synchronously during testing
        settings.CELERY_TASK_ALWAYS_EAGER = True
        self.image_sizes = settings.IMAGE_SIZES

    def create_video(self, **kwargs):
        # create an instance
        factory_instance = factories.VideoFactory.create(**kwargs)

        # retrieve a fresh copy after thumbnail generation task has run
        # (synchronously but still not reflected in the factory return value)
        return Video.objects.get(id=factory_instance.id)

    def get_video_dimensions(self, video_size):
        dimensions = self.video_dimensions[video_size]
        return {"width": dimensions[0], "height": dimensions[1]}

    def create_site_and_video(self, video_size="medium-square"):
        with patch(
            "backend.models.media.VideoFile.get_video_info"
        ) as mock_get_video_info:
            mock_get_video_info.return_value = self.get_video_dimensions(video_size)
            site = factories.SiteFactory.create()

            video_file = factories.VideoFileFactory.create(
                content=get_video_content(video_size)
            )

            video = self.create_video(site=site, original=video_file)
            return site, video

    @pytest.mark.django_db
    def test_related_file_removed_on_delete(self):
        media_instance = self.create_video()
        related_id = media_instance.original.id
        related_image_ids = [
            media_instance.thumbnail.id,
            media_instance.small.id,
            media_instance.medium.id,
        ]
        assert VideoFile.objects.filter(pk=related_id).count() == 1
        for related_id in related_image_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 1

        media_instance.delete()

        assert VideoFile.objects.filter(pk=related_id).count() == 0
        for related_id in related_image_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 0

    @pytest.mark.django_db
    def test_related_file_removed_on_update(self):
        media_instance = self.create_video()
        related_id = media_instance.original.id
        related_image_ids = [
            media_instance.thumbnail.id,
            media_instance.small.id,
            media_instance.medium.id,
        ]
        assert VideoFile.objects.filter(pk=related_id).count() == 1
        for related_id in related_image_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 1

        media_instance.original = factories.VideoFileFactory.create()
        media_instance.save()

        assert VideoFile.objects.filter(pk=related_id).count() == 0
        for related_id in related_image_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 0

    @pytest.mark.django_db
    def test_update_video_file_not_supported(self):
        media_instance = self.create_video()
        try:
            new_content = get_video_content("small")
            media_instance.original.content = new_content
            media_instance.original.save()
            assert False
        except NotSupportedError:
            assert True

    @pytest.mark.parametrize("video_shape", ["portrait", "landscape", "square"])
    @pytest.mark.parametrize("video_size", ["thumbnail", "small", "medium", "large"])
    @pytest.mark.django_db
    def test_thumbnails_never_bigger_than_original(self, video_shape, video_size):
        site, video = self.create_site_and_video(f"{video_size}-{video_shape}")

        for size_name in self.size_names:
            generated_image = getattr(video, size_name)
            assert generated_image.width <= video.original.width
            assert generated_image.height <= video.original.height

    @pytest.mark.parametrize("video_shape", ["portrait", "landscape", "square"])
    @pytest.mark.parametrize("video_size", ["thumbnail", "small", "medium", "large"])
    @pytest.mark.django_db
    def test_thumbnails_never_bigger_than_size_settings(self, video_shape, video_size):
        site, video = self.create_site_and_video(f"{video_size}-{video_shape}")

        for size_name in self.size_names:
            generated_image = getattr(video, size_name)
            size_setting = self.image_sizes[size_name]
            assert generated_image.width <= size_setting
            assert generated_image.height <= size_setting

    @pytest.mark.parametrize("video_shape", ["portrait", "landscape", "square"])
    @pytest.mark.django_db
    def test_thumbnails_as_big_as_possible(self, video_shape):
        site, video = self.create_site_and_video(f"large-{video_shape}")

        for index, size_name in enumerate(self.size_names):
            if index > 0:
                generated_image = getattr(video, size_name)
                smaller_size = self.size_names[index - 1]
                smaller_size_setting = self.image_sizes[smaller_size]
                assert (generated_image.width > smaller_size_setting) | (
                    generated_image.height > smaller_size_setting
                )

    @pytest.mark.parametrize(
        "video_shape",
        ["portrait", "landscape", "portrait-extreme", "landscape-extreme", "square"],
    )
    @pytest.mark.parametrize("video_size", ["thumbnail", "small", "medium", "large"])
    @pytest.mark.django_db
    def test_thumbnails_always_proportional(self, video_shape, video_size):
        site, video = self.create_site_and_video(f"{video_size}-{video_shape}")

        video_proportion_ratio = video.original.height / video.original.width

        for size_name in self.size_names:
            # getting weird results here, possibly because mocking is affecting the dimensions that are saved on
            # the thumbnail models
            # see if it can be fixed without really using ffmpeg
            # also check whether there are any real problems with the thumbnail dimension calculations
            generated_image = getattr(video, size_name)
            generated_image_ratio = generated_image.height / generated_image.width
            assert abs(generated_image_ratio - video_proportion_ratio) < 0.1

    @pytest.mark.django_db
    def test_thumbnail_paths_correct(self):
        site, video = self.create_site_and_video()

        for size_name in self.image_sizes:
            generated_image = getattr(video, size_name)
            assert generated_image.content.file
            assert f"{site.slug}/" in generated_image.content.path
            assert f"_{size_name}" in generated_image.content.path

    @pytest.mark.django_db
    def test_ffmpeg_probe_returning_none(self, caplog):
        caplog.set_level(logging.WARNING)
        video = factories.VideoFileFactory.create()
        with patch(
            "backend.models.media.VideoFile.get_video_info"
        ) as mock_get_video_info:
            mock_get_video_info.return_value = None
            video.save(update_metadata_command=True)
            assert (
                f"Failed to get video info for [{video.content.name}]. \n"
                in caplog.text
            )


class TestImageModel:
    image_sizes = None
    size_names = ["thumbnail", "small", "medium"]

    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        # Runs the thumbnail generation synchronously during testing
        settings.CELERY_TASK_ALWAYS_EAGER = True
        self.image_sizes = settings.IMAGE_SIZES

    def create_image(self, **kwargs):
        # create an instance
        factory_instance = factories.ImageFactory.create(**kwargs)

        # retrieve a fresh copy after thumbnail generation task has run
        # (synchronously but still not reflected in the factory return value)
        return Image.objects.get(id=factory_instance.id)

    @pytest.mark.django_db
    def test_related_files_removed_on_delete(self):
        media_instance = self.create_image()
        related_ids = [
            media_instance.original.id,
            media_instance.thumbnail.id,
            media_instance.small.id,
            media_instance.medium.id,
        ]

        for related_id in related_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 1

        media_instance.delete()

        for related_id in related_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 0

    @pytest.mark.django_db
    def test_related_files_removed_on_update(self):
        media_instance = self.create_image()
        related_ids = [
            media_instance.original.id,
            media_instance.thumbnail.id,
            media_instance.small.id,
            media_instance.medium.id,
        ]

        for related_id in related_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 1

        media_instance.original = factories.ImageFileFactory.create()
        media_instance.save()

        for related_id in related_ids:
            assert ImageFile.objects.filter(pk=related_id).count() == 0

    @pytest.mark.parametrize("thumbnail_field", size_names)
    @pytest.mark.django_db
    def test_resized_images_wide(self, thumbnail_field):
        site = factories.SiteFactory.create()

        # Check resizing when the width of the input image is larger
        wide_image_file = factories.ImageFileFactory.create(
            content=factory.django.ImageField(width=1200, height=600), site=site
        )
        image = self.create_image(site=site, original=wide_image_file)
        thumbnail = getattr(image, thumbnail_field)
        generated_image = thumbnail.content
        assert generated_image.file
        # assert f"/{site.slug}/" in generated_image.path
        assert f"_{thumbnail_field}" in generated_image.path
        assert generated_image.width == self.image_sizes[thumbnail_field]
        assert generated_image.height == self.image_sizes[thumbnail_field] / 2

    @pytest.mark.parametrize("thumbnail_field", size_names)
    @pytest.mark.django_db
    def test_resized_images_tall(self, thumbnail_field):
        site = factories.SiteFactory.create()

        # Check resized images when the height of the input image is larger
        tall_image_file = factories.ImageFileFactory.create(
            content=factory.django.ImageField(width=600, height=1200), site=site
        )

        image = self.create_image(site=site, original=tall_image_file)
        thumbnail = getattr(image, thumbnail_field)
        generated_image = thumbnail.content
        assert generated_image.file
        assert f"/{site.slug}/" in generated_image.path
        assert f"_{thumbnail_field}" in generated_image.path
        assert generated_image.width == self.image_sizes[thumbnail_field] / 2
        assert generated_image.height == self.image_sizes[thumbnail_field]


class TestEmbeddedVideoModel:
    @pytest.mark.parametrize(
        "url",
        ["", "not valid", "https://www.invalid-url.com/", "https://soundcloud.com/"],
    )
    @pytest.mark.django_db
    def test_embeded_invalid_base_site(self, url):
        site = factories.SiteFactory.create()

        try:
            content_field = EmbedVideoField(url)
            embedded_video = factories.EmbeddedVideoFactory.create(
                site=site, content=content_field
            )
            detect_backend(embedded_video.content.verbose_name)
            assert False
        except UnknownBackendException:
            assert True

    @pytest.mark.parametrize(
        "url, backend_class",
        [
            ("https://www.youtube.com/", YoutubeBackend),
            ("https://vimeo.com/", VimeoBackend),
        ],
    )
    @pytest.mark.django_db
    def test_embeded_valid_base_site(self, url, backend_class):
        site = factories.SiteFactory.create()

        try:
            content_field = EmbedVideoField(url)
            embedded_video = factories.EmbeddedVideoFactory.create(
                site=site, content=content_field
            )
            backend = detect_backend(embedded_video.content.verbose_name)
            assert isinstance(backend, backend_class)
        except UnknownBackendException:
            assert False
