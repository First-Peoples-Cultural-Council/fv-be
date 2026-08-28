from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

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

    def create_media_with_null_original(self):
        """Creates one instance of each media type with a null original file."""
        return {
            model.__name__: factory.create(site=self.site, original=None)
            for model, factory in self.MEDIA_TYPES
        }

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

    def test_dry_run(self, tmp_path, caplog):
        self.create_media_with_null_original()

        call_command(
            "delete_null_original_media", output_dir=str(tmp_path), dry_run=True
        )

        for model, _ in self.MEDIA_TYPES:
            assert model.objects.count() == 1

        self.assert_caplog_text(caplog)
        assert "Dry run mode enabled. No changes will be made" in caplog.text
        for model, _ in self.MEDIA_TYPES:
            assert (
                f"[Dry Run] Would delete 1 {model.__name__} records with null original."
                in caplog.text
            )
        assert "Change log written to" not in caplog.text

    def test_delete_null_original_media(self, tmp_path, caplog):
        self.create_media_with_null_original()

        call_command("delete_null_original_media", output_dir=str(tmp_path))

        for model, _ in self.MEDIA_TYPES:
            assert model.objects.count() == 0

        self.assert_caplog_text(caplog)
        for model, _ in self.MEDIA_TYPES:
            assert (
                f"Deleting 1 {model.__name__} record(s) with null original."
                in caplog.text
            )

    def test_only_null_original_media_deleted(self, tmp_path, caplog):
        kept = self.create_media_with_original()
        self.create_media_with_null_original()

        call_command("delete_null_original_media", output_dir=str(tmp_path))

        for model, _ in self.MEDIA_TYPES:
            assert model.objects.count() == 1
            assert model.objects.filter(id=kept[model.__name__].id).exists()

    def test_change_log_written(self, tmp_path, caplog):
        deleted = self.create_media_with_null_original()

        call_command("delete_null_original_media", output_dir=str(tmp_path))

        output_file = (
            tmp_path
            / f"delete_null_original_media_log_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        assert output_file.exists()

        with open(output_file) as f:
            content = f.read()

        expected_content = ["model,id,title,site"] + [
            f"{model.__name__},{deleted[model.__name__].id},"
            f"{deleted[model.__name__].title},{self.site.slug}"
            for model, _ in self.MEDIA_TYPES
        ]

        actual_content = [line.strip() for line in content.splitlines()]
        assert set(actual_content) == set(expected_content)
        assert f"Change log written to {output_file}" in caplog.text

    def test_rollback_if_error(self, tmp_path):
        self.create_media_with_null_original()

        with patch.object(Video, "delete", side_effect=Exception("Mocked exception")):
            with pytest.raises(Exception, match="Mocked exception"):
                call_command("delete_null_original_media", output_dir=str(tmp_path))

        for model, _ in self.MEDIA_TYPES:
            assert model.objects.count() == 1
