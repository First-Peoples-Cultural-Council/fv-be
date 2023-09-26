import logging
import os

import factory
import ffmpeg
import pytest
from django.conf import settings
from django.db import NotSupportedError
from embed_video.backends import (
    UnknownBackendException,
    VimeoBackend,
    YoutubeBackend,
    detect_backend,
)
from embed_video.fields import EmbedVideoField

from backend.models.media import File, ImageFile, VideoFile
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
        # Factories don't use InMemoryUploadedFiles like the live code, so dimensions don't work in tests
        # assert instance.height == 100
        # assert instance.width == 100

    @pytest.mark.django_db
    def test_videofile_generated_properties(self):
        # Dimensions are from conftest.py/mock_get_video_dimensions
        site = factories.SiteFactory.create()
        instance = factories.VideoFileFactory.create(site=site)
        assert instance.mimetype == "video/mp4"
        assert instance.height == 100
        assert instance.width == 100

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


@pytest.mark.skip("Most of this is not compatible with async generation")
class TestVideoModel:
    image_sizes = list(settings.IMAGE_SIZES.keys())

    def check_image(self, video, site):
        """
        A helper function to get, check, and return the generated images for a Video model
        """

        generated_images = [
            getattr(video, "thumbnail"),
            getattr(video, "small"),
            getattr(video, "medium"),
        ]
        for index, generated_image in enumerate(generated_images):
            assert generated_image.content.file
            assert f"{site.slug}/" in generated_image.content.path
            assert f"_{self.image_sizes[index]}" in generated_image.content.path

        return generated_images

    def get_video_dimensions(self, video_size):
        """
        A helper function to read the video width and height from the file
        """
        path = (
            os.path.dirname(os.path.realpath(__file__))
            + f"/../factories/resources/video_example_{video_size}.mp4"
        )
        probe = ffmpeg.probe(path)
        video_stream = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "video"),
            None,
        )
        width = int(video_stream["width"])
        height = int(video_stream["height"])
        return {"width": width, "height": height}

    def create_site_and_video(self, video_size):
        site = factories.SiteFactory.create()

        video_file = factories.VideoFileFactory.create(
            content=get_video_content(video_size)
        )
        video = factories.VideoFactory.create(site=site, original=video_file)
        return site, video

    @pytest.mark.django_db
    def test_related_file_removed_on_delete(self):
        media_instance = factories.VideoFactory.create()
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
        media_instance = factories.VideoFactory.create()
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
        media_instance = factories.VideoFactory.create()
        try:
            new_content = get_video_content("small")
            media_instance.original.content = new_content
            media_instance.original.save()
            assert False
        except NotSupportedError:
            assert True

    @pytest.mark.django_db
    def test_resize_images_large_input_video(self):
        site, video = self.create_site_and_video("large")

        generated_images = self.check_image(video, site)

        assert generated_images[2].width == settings.IMAGE_SIZES["medium"]
        assert (
            settings.IMAGE_SIZES["small"]
            < generated_images[2].height
            <= settings.IMAGE_SIZES["medium"]
        )
        assert (
            settings.IMAGE_SIZES["thumbnail"]
            < generated_images[1].width
            <= settings.IMAGE_SIZES["small"]
        )
        assert (
            settings.IMAGE_SIZES["thumbnail"]
            < generated_images[1].height
            <= settings.IMAGE_SIZES["small"]
        )
        assert generated_images[0].width <= settings.IMAGE_SIZES["thumbnail"]
        assert generated_images[0].height <= settings.IMAGE_SIZES["thumbnail"]

    @pytest.mark.django_db
    def test_resize_images_medium_input_video(self):
        site, video = self.create_site_and_video("medium")
        video_dimensions = self.get_video_dimensions("medium")

        generated_images = self.check_image(video, site)

        assert generated_images[2].width == video_dimensions["width"]
        assert generated_images[2].height == video_dimensions["height"]
        assert generated_images[1].width == settings.IMAGE_SIZES["small"]
        assert (
            settings.IMAGE_SIZES["thumbnail"]
            < generated_images[1].height
            <= settings.IMAGE_SIZES["small"]
        )
        assert generated_images[0].width <= settings.IMAGE_SIZES["thumbnail"]
        assert generated_images[0].height <= settings.IMAGE_SIZES["thumbnail"]

    @pytest.mark.django_db
    def test_resize_images_small_input_video(self):
        site, video = self.create_site_and_video("small")
        video_dimensions = self.get_video_dimensions("small")

        generated_images = self.check_image(video, site)

        assert generated_images[1].width == video_dimensions["width"]
        assert generated_images[1].height == video_dimensions["height"]
        assert generated_images[1].width == video_dimensions["width"]
        assert generated_images[1].height == video_dimensions["height"]
        assert generated_images[0].width == settings.IMAGE_SIZES["thumbnail"]
        assert generated_images[0].height <= settings.IMAGE_SIZES["thumbnail"]

    @pytest.mark.django_db
    def test_resize_images_thumbnail_input_video(self):
        site, video = self.create_site_and_video("thumbnail")
        video_dimensions = self.get_video_dimensions("thumbnail")

        generated_images = self.check_image(video, site)

        assert generated_images[2].width == video_dimensions["width"]
        assert generated_images[2].height == video_dimensions["height"]
        assert generated_images[1].width == video_dimensions["width"]
        assert generated_images[1].height == video_dimensions["height"]
        assert generated_images[0].width == video_dimensions["width"]
        assert generated_images[0].height == video_dimensions["height"]

    @pytest.mark.django_db
    def test_resize_images_large_rotated_input_video(self):
        site, video = self.create_site_and_video("large_rotated")

        generated_images = self.check_image(video, site)

        assert (
            settings.IMAGE_SIZES["small"]
            < generated_images[2].width
            <= settings.IMAGE_SIZES["medium"]
        )
        assert (
            settings.IMAGE_SIZES["medium"] - 2
            < generated_images[2].height
            < settings.IMAGE_SIZES["medium"] + 2
        )
        assert (
            settings.IMAGE_SIZES["thumbnail"]
            < generated_images[1].width
            <= settings.IMAGE_SIZES["small"]
        )
        assert (
            settings.IMAGE_SIZES["thumbnail"]
            < generated_images[1].height
            <= settings.IMAGE_SIZES["small"]
        )
        assert generated_images[0].width <= settings.IMAGE_SIZES["thumbnail"]
        assert generated_images[0].height <= settings.IMAGE_SIZES["thumbnail"]


@pytest.mark.skip("Most of this is not compatible with async generation")
class TestImageModel:
    image_sizes = list(settings.IMAGE_SIZES.keys())

    @pytest.mark.django_db
    def test_related_files_removed_on_delete(self):
        media_instance = factories.ImageFactory.create()
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
        media_instance = factories.ImageFactory.create()
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

    @pytest.mark.parametrize("thumbnail_field", image_sizes)
    @pytest.mark.django_db
    def test_resized_images_wide(self, thumbnail_field):
        site = factories.SiteFactory.create()

        # Check resizing when the width of the input image is larger
        wide_image_file = factories.ImageFileFactory.create(
            content=factory.django.ImageField(width=1200, height=600), site=site
        )
        image = factories.ImageFactory.create(site=site, original=wide_image_file)
        thumbnail = getattr(image, thumbnail_field)
        generated_image = thumbnail.content
        assert generated_image.file
        assert f"/{site.slug}/" in generated_image.path
        assert f"_{thumbnail_field}" in generated_image.path
        assert generated_image.width == settings.IMAGE_SIZES[thumbnail_field]
        assert generated_image.height == settings.IMAGE_SIZES[thumbnail_field] / 2

    @pytest.mark.parametrize("thumbnail_field", image_sizes)
    @pytest.mark.django_db
    def test_resized_images_tall(self, thumbnail_field):
        site = factories.SiteFactory.create()

        # Check resized images when the height of the input image is larger
        tall_image_file = factories.ImageFileFactory.create(
            content=factory.django.ImageField(width=600, height=1200), site=site
        )

        image = factories.ImageFactory.create(site=site, original=tall_image_file)
        thumbnail = getattr(image, thumbnail_field)
        generated_image = thumbnail.content
        assert generated_image.file
        assert f"/{site.slug}/" in generated_image.path
        assert f"_{thumbnail_field}" in generated_image.path
        assert generated_image.width == settings.IMAGE_SIZES[thumbnail_field] / 2
        assert generated_image.height == settings.IMAGE_SIZES[thumbnail_field]


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
