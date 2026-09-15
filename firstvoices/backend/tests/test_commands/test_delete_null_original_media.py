import pytest
from django.core.management import call_command

from backend.models.media import Audio, Document, Image, Video
from backend.tests import factories


@pytest.mark.django_db
class TestDeleteNullOriginalMedia:
    # (model, factory) pairs for each media type the command cleans up
    MEDIA_TYPES = [
        (Audio, factories.AudioFactory),
        (Document, factories.DocumentFactory),
        (Image, factories.ImageFactory),
        (Video, factories.VideoFactory),
    ]

    def setup_method(self):
        self.site = factories.SiteFactory()

    def create_media_with_original(self):
        """Creates one instance of each media type with a valid original file."""
        return {
            model.__name__: factory.create(site=self.site)
            for model, factory in self.MEDIA_TYPES
        }

    @staticmethod
    def assert_caplog_text(caplog):
        assert "Starting to delete media with null original files." in caplog.text
        assert "Finished deleting media with null original files." in caplog.text

    def test_invalid_output_dir(self, caplog):
        call_command("delete_null_original_media", output_dir="invalid/dir")
        assert (
            "Output directory 'invalid/dir' does not exist or is not writeable."
            in caplog.text
        )

    def test_no_null_original_media(self, tmp_path, caplog):
        self.create_media_with_original()

        call_command("delete_null_original_media", output_dir=str(tmp_path))

        for model, _ in self.MEDIA_TYPES:
            assert model.objects.count() == 1

        self.assert_caplog_text(caplog)
        assert "Change log written to" not in caplog.text
