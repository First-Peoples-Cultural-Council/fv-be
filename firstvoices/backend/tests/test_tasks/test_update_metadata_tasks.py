import logging
from unittest.mock import patch

import pytest
from django.core import management

from backend.models.media import File, ImageFile, VideoFile
from backend.tasks.update_metadata_tasks import (
    update_missing_audio_metadata,
    update_missing_image_metadata,
    update_missing_video_metadata,
)
from backend.tests import factories


class TestUpdateMetadataTasks:
    @pytest.mark.parametrize(
        "empty_field_name, expected_value",
        [("mimetype", "image/jpeg"), ("size", 818), ("width", 100), ("height", 100)],
    )
    @pytest.mark.django_db
    def test_update_missing_image_metadata(self, empty_field_name, expected_value):
        site = factories.SiteFactory.create()
        image = factories.ImageFileFactory.create(site=site)
        ImageFile.objects.filter(pk=image.pk).update(**{empty_field_name: None})

        image = ImageFile.objects.get(pk=image.pk)
        assert getattr(image, empty_field_name) is None

        update_missing_image_metadata()

        image = ImageFile.objects.get(pk=image.pk)

        if empty_field_name == "size":
            assert abs(getattr(image, empty_field_name) - expected_value) <= 10
        else:
            assert getattr(image, empty_field_name) == expected_value

    @pytest.mark.parametrize(
        "empty_field_name, expected_value",
        [("mimetype", "video/mp4"), ("size", 6415), ("width", 100), ("height", 100)],
    )
    @pytest.mark.django_db
    def test_update_missing_video_metadata(self, empty_field_name, expected_value):
        site = factories.SiteFactory.create()
        video = factories.VideoFileFactory.create(site=site)
        VideoFile.objects.filter(pk=video.pk).update(**{empty_field_name: None})

        video = VideoFile.objects.get(pk=video.pk)
        assert getattr(video, empty_field_name) is None

        update_missing_video_metadata()

        video = VideoFile.objects.get(pk=video.pk)

        assert getattr(video, empty_field_name) == expected_value

    @pytest.mark.parametrize(
        "empty_field_name, expected_value",
        [("mimetype", "application/x-empty"), ("size", 0)],
    )
    @pytest.mark.django_db
    def test_update_missing_audio_metadata(self, empty_field_name, expected_value):
        site = factories.SiteFactory.create()
        audio = factories.FileFactory.create(site=site)
        File.objects.filter(pk=audio.pk).update(**{empty_field_name: None})

        audio = File.objects.get(pk=audio.pk)
        assert getattr(audio, empty_field_name) is None

        update_missing_audio_metadata()

        audio = File.objects.get(pk=audio.pk)

        assert getattr(audio, empty_field_name) == expected_value

    @pytest.mark.django_db
    def test_no_image_metadata_to_update_and_save_not_called(self):
        site = factories.SiteFactory.create()
        factories.ImageFileFactory.create(site=site)

        assert ImageFile.objects.count() == 1

        with patch("backend.models.media.ImageFile.save") as mock_save:
            update_missing_image_metadata()
            assert not mock_save.called

    @pytest.mark.django_db
    def test_no_video_metadata_to_update_and_save_not_called(self):
        site = factories.SiteFactory.create()
        factories.VideoFileFactory.create(site=site)

        assert VideoFile.objects.count() == 1

        with patch("backend.models.media.VideoFile.save") as mock_save:
            update_missing_video_metadata()
            assert not mock_save.called

    @pytest.mark.django_db
    def test_no_audio_metadata_to_update_and_save_not_called(self):
        site = factories.SiteFactory.create()
        factories.FileFactory.create(site=site)

        assert File.objects.count() == 1

        with patch("backend.models.media.File.save") as mock_save:
            update_missing_audio_metadata()
            assert not mock_save.called

    @pytest.mark.django_db
    def test_image_file_not_found(self, caplog):
        caplog.set_level(logging.WARNING)
        site = factories.SiteFactory.create()
        image = factories.ImageFileFactory.create(site=site)
        ImageFile.objects.filter(pk=image.pk).update(mimetype=None)

        with patch(
            "backend.models.media.ImageFile.save", side_effect=FileNotFoundError()
        ):
            update_missing_image_metadata()
            assert f"File not found for ImageFile {image.id}." in caplog.text

    @pytest.mark.django_db
    def test_video_file_not_found(self, caplog):
        caplog.set_level(logging.WARNING)
        site = factories.SiteFactory.create()
        video = factories.VideoFileFactory.create(site=site)
        VideoFile.objects.filter(pk=video.pk).update(mimetype=None)

        with patch(
            "backend.models.media.VideoFile.save", side_effect=FileNotFoundError()
        ):
            update_missing_video_metadata()
            assert f"File not found for VideoFile {video.id}." in caplog.text

    @pytest.mark.django_db
    def test_audio_file_not_found(self, caplog):
        caplog.set_level(logging.WARNING)
        site = factories.SiteFactory.create()
        audio = factories.FileFactory.create(site=site)
        File.objects.filter(pk=audio.pk).update(mimetype=None)

        with patch("backend.models.media.File.save", side_effect=FileNotFoundError()):
            update_missing_audio_metadata()
            assert f"File not found for audio File {audio.id}." in caplog.text

    def test_command(self):
        with patch(
            "backend.tasks.update_metadata_tasks.update_missing_image_metadata.apply_async"
        ) as mock_image, patch(
            "backend.tasks.update_metadata_tasks.update_missing_video_metadata.apply_async"
        ) as mock_video, patch(
            "backend.tasks.update_metadata_tasks.update_missing_audio_metadata.apply_async"
        ) as mock_audio:
            management.call_command("update_missing_media_metadata")
            assert mock_image.called
            assert mock_video.called
            assert mock_audio.called
