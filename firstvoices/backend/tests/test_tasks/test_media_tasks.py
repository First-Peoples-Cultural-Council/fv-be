from unittest.mock import patch

import pytest
from PIL import Image as PILImage

from backend.models.media import SUPPORTED_FILETYPES, Image, Video
from backend.tasks.media_tasks import generate_media_thumbnails
from backend.tests.factories import (
    ImageFactory,
    ImageFileFactory,
    SiteFactory,
    VideoFactory,
    VideoFileFactory,
    get_image_content,
)
from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin


class TestThumbnailGeneration(IgnoreTaskResultsMixin):
    TASK = generate_media_thumbnails

    def get_valid_task_args(self):
        image = ImageFactory.create()
        return image._meta.model_name, image.id

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    @pytest.mark.parametrize(
        "model_factory, model", [(ImageFactory, "image"), (VideoFactory, "video")]
    )
    def test_thumbnail_generation_started(self, model_factory, model, caplog):
        site = SiteFactory()
        media_item = model_factory.create(site=site)

        assert (
            f"Task started. Additional info: "
            f"model_name: {model}, instance_id: {media_item.id}." in caplog.text
        )
        assert "Task ended." in caplog.text

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    @pytest.mark.parametrize(
        "model, model_factory, model_file_factory",
        [
            (Image, ImageFactory, ImageFileFactory),
            (Video, VideoFactory, VideoFileFactory),
        ],
    )
    def test_thumbnail_generation_does_not_update_last_modified(
        self, model, model_factory, model_file_factory
    ):
        site = SiteFactory()

        media_file = model_file_factory.create()
        media_item = model_factory.create(site=site, original=media_file)
        original_last_modified = media_item.last_modified

        media_item._request_thumbnail_generation()

        media_item = model.objects.get(id=media_item.id)

        new_last_modified = media_item.last_modified

        assert new_last_modified == original_last_modified

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    @pytest.mark.parametrize("file_type", SUPPORTED_FILETYPES["image"])
    def test_thumbnail_generation_adds_white_background(self, file_type):
        site = SiteFactory()
        image_file = ImageFileFactory.create(
            content=get_image_content(file_type=file_type),
            site=site,
        )
        image = ImageFactory.create(original=image_file, site=site)

        image.generate_resized_images()
        image.refresh_from_db()

        with PILImage.open(image.medium.content) as img:
            assert img.getpixel((0, 0)) >= (250, 250, 250)

        with PILImage.open(image.small.content) as img:
            assert img.getpixel((0, 0)) >= (250, 250, 250)

        with PILImage.open(image.thumbnail.content) as img:
            assert img.getpixel((0, 0)) >= (250, 250, 250)

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_thumbail_generation_error(self, caplog):
        site = SiteFactory()
        image = ImageFactory.create(site=site)

        with patch(
            "PIL.Image.open",
            side_effect=Exception("test exception"),
        ):
            image._request_thumbnail_generation()

        assert "Error creating thumbnail for " in caplog.text
        assert "test exception" in caplog.text
