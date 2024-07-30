import pytest

from backend.models.media import Image, Video
from backend.tests.factories import (
    ImageFactory,
    ImageFileFactory,
    SiteFactory,
    VideoFactory,
    VideoFileFactory,
)


class TestThumbnailGeneration:
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

        media_item = model.objects.get(id=media_item.id)

        new_last_modified = media_item.last_modified

        assert new_last_modified == original_last_modified
