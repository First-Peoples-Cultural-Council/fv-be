import factory
import pytest
from django.conf import settings
from embed_video.backends import (
    UnknownBackendException,
    VimeoBackend,
    YoutubeBackend,
    detect_backend,
)
from embed_video.fields import EmbedVideoField

from backend.models.media import File, ImageFile, VideoFile
from backend.tests import factories


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
    @pytest.mark.django_db
    def test_related_file_removed_on_delete(self):
        media_instance = factories.VideoFactory.create()
        related_id = media_instance.original.id
        assert VideoFile.objects.filter(pk=related_id).count() == 1

        media_instance.delete()

        assert VideoFile.objects.filter(pk=related_id).count() == 0

    @pytest.mark.django_db
    def test_related_file_removed_on_update(self):
        media_instance = factories.VideoFactory.create()
        related_id = media_instance.original.id
        assert VideoFile.objects.filter(pk=related_id).count() == 1

        media_instance.original = factories.VideoFileFactory.create()
        media_instance.save()

        assert VideoFile.objects.filter(pk=related_id).count() == 0


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
