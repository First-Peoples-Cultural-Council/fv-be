from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command

from backend.models.files import File
from backend.models.media import ImageFile, VideoFile
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestUpdateFileSizes:

    @staticmethod
    def setup_files_with_missing_sizes(site):
        file = factories.FileFactory.create(
            site=site,
            content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
        )
        imagefile = factories.ImageFileFactory.create(
            site=site,
            content=get_sample_file("sample-image.jpg", "image/jpeg"),
        )
        videofile = factories.VideoFileFactory.create(
            site=site,
            content=get_sample_file("video_example_small.mp4", "video/mp4"),
        )

        File.objects.filter(id=file.id).update(size=None)
        ImageFile.objects.filter(id=imagefile.id).update(size=None)
        VideoFile.objects.filter(id=videofile.id).update(size=None)

        file.refresh_from_db()
        imagefile.refresh_from_db()
        videofile.refresh_from_db()

        assert file.size is None
        assert imagefile.size is None
        assert videofile.size is None

        return file, imagefile, videofile

    def setup_file_missing_content(self, site):
        empty_file = ContentFile(b"", name="empty_file.txt")
        file = factories.FileFactory.create(
            site=site,
            content=empty_file,
        )
        return file

    @staticmethod
    def assert_caplog_text(caplog, site_slugs):
        for slug in site_slugs:
            assert f"Updating file sizes for media files in {slug}..." in caplog.text
            assert f"Completed updating file sizes for site {slug}." in caplog.text

        assert "File size update process completed for all sites." in caplog.text

    def test_update_file_sizes_no_site(self, caplog):
        call_command("update_file_sizes", site_slugs="invalid-site")
        assert "No sites with the provided slug(s) found." in caplog.text

    def test_update_file_sizes_single_site(self, caplog):
        site = factories.SiteFactory.create()
        file, imagefile, videofile = self.setup_files_with_missing_sizes(site)

        call_command("update_file_sizes", site_slugs=site.slug)

        self.assert_caplog_text(caplog, [site.slug])

        file.refresh_from_db()
        imagefile.refresh_from_db()
        videofile.refresh_from_db()

        assert file.size == file.content.size
        assert imagefile.size == imagefile.content.size
        assert videofile.size == videofile.content.size

    def test_update_file_sizes_all_sites(self, caplog):
        site1 = factories.SiteFactory.create()
        site2 = factories.SiteFactory.create()
        file1, imagefile1, videofile1 = self.setup_files_with_missing_sizes(site1)
        file2, imagefile2, videofile2 = self.setup_files_with_missing_sizes(site2)

        call_command("update_file_sizes")

        self.assert_caplog_text(caplog, [site1.slug, site2.slug])

        file1.refresh_from_db()
        imagefile1.refresh_from_db()
        videofile1.refresh_from_db()
        file2.refresh_from_db()
        imagefile2.refresh_from_db()
        videofile2.refresh_from_db()

        assert file1.size == file1.content.size
        assert imagefile1.size == imagefile1.content.size
        assert videofile1.size == videofile1.content.size
        assert file2.size == file2.content.size
        assert imagefile2.size == imagefile2.content.size
        assert videofile2.size == videofile2.content.size

    def test_update_file_sizes_missing_content(self, caplog):
        site = factories.SiteFactory.create()
        file = self.setup_file_missing_content(site)

        call_command("update_file_sizes", site_slugs=site.slug)

        assert f"File size not found for File with ID {file.id}" in caplog.text

        file.refresh_from_db()
        assert file.size == 0

    def test_rollback_on_error(self, caplog):
        site = factories.SiteFactory.create()
        file, imagefile, videofile = self.setup_files_with_missing_sizes(site)

        file.refresh_from_db()
        imagefile.refresh_from_db()
        videofile.refresh_from_db()

        with patch(
            "backend.management.commands.update_file_sizes.Command.update_file_size",
            side_effect=Exception("Mocked exception"),
        ):
            with pytest.raises(Exception, match="Mocked exception"):
                call_command("update_file_sizes", site_slugs=site.slug)

        file.refresh_from_db()
        imagefile.refresh_from_db()
        videofile.refresh_from_db()

        assert file.size is None
        assert imagefile.size is None
        assert videofile.size is None

    def test_timestamps(self):
        # ensure last_modified is not updated, and that system_last_modified is updated
        site = factories.SiteFactory.create()
        file, imagefile, videofile = self.setup_files_with_missing_sizes(site)

        old_last_modified = file.last_modified
        old_image_last_modified = imagefile.last_modified
        old_video_last_modified = videofile.last_modified

        call_command("update_file_sizes", site_slugs=site.slug)
        file.refresh_from_db()
        imagefile.refresh_from_db()
        videofile.refresh_from_db()

        assert file.last_modified == old_last_modified
        assert imagefile.last_modified == old_image_last_modified
        assert videofile.last_modified == old_video_last_modified

        assert file.system_last_modified != file.last_modified
        assert file.system_last_modified > file.last_modified

        assert imagefile.system_last_modified != imagefile.last_modified
        assert imagefile.system_last_modified > imagefile.last_modified

        assert videofile.system_last_modified != videofile.last_modified
        assert videofile.system_last_modified > videofile.last_modified
