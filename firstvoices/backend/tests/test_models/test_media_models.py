import factory
import pytest
from django.conf import settings

from backend.tests import factories


class TestMediaModels:
    media_factories = [
        factories.ImageFactory,
        factories.AudioFactory,
        factories.VideoFactory,
    ]

    @pytest.mark.parametrize("media_factory", media_factories)
    @pytest.mark.django_db
    def test_upload_folder(self, media_factory):
        site = factories.SiteFactory.create()
        media_instance = media_factory.create(site=site)
        media_file = media_instance.content
        assert media_file.file
        assert f"/{site.slug}/" in media_file.path

    @pytest.mark.parametrize("media_factory", media_factories)
    @pytest.mark.django_db
    def test_file_deleted(self, media_factory):
        media_instance = media_factory.create()
        media_file = media_instance.content
        assert media_file.file

        media_instance.delete()

        try:
            media_file.file
            assert False
        except ValueError:
            assert True


class TestImageModel:
    image_sizes = list(settings.IMAGE_SIZES.keys())

    @pytest.mark.parametrize("image_size", image_sizes)
    @pytest.mark.django_db
    def test_resized_images(self, image_size):
        site = factories.SiteFactory.create()

        # Check resizing when the width of the input image is larger
        image = factories.ImageFactory.create(
            site=site, content=factory.django.ImageField(width=1200, height=600)
        )
        generated_image = getattr(image, image_size)
        assert generated_image.file
        assert f"/{site.slug}/" in generated_image.path
        assert f"_{image_size}" in generated_image.path
        assert generated_image.width == settings.IMAGE_SIZES[image_size]
        assert generated_image.height == settings.IMAGE_SIZES[image_size] / 2

        # Check resized images when the height of the input image is larger
        image_two = factories.ImageFactory.create(
            site=site, content=factory.django.ImageField(width=600, height=1200)
        )
        generated_image_two = getattr(image_two, image_size)
        assert generated_image_two.file
        assert f"/{site.slug}/" in generated_image_two.path
        assert f"_{image_size}" in generated_image_two.path
        assert generated_image_two.width == settings.IMAGE_SIZES[image_size] / 2
        assert generated_image_two.height == settings.IMAGE_SIZES[image_size]
