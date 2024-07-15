import pytest

from backend.tests.factories import ImageFactory, SiteFactory, VideoFactory


class TestThumbnailGeneration:
    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    @pytest.mark.parametrize(
        "model_factory, model", [(ImageFactory, "image"), (VideoFactory, "video")]
    )
    def test_thumbnail_generation_started(self, model_factory, model, caplog):
        site = SiteFactory()
        media_item = model_factory.create(site=site, title="Test media item")

        assert (
            f"Task started. Additional info: "
            f"model_name: {model}, instance_id: {media_item.id}." in caplog.text
        )
        assert "Task ended." in caplog.text
