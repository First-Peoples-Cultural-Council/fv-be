from unittest.mock import Mock, PropertyMock, patch

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command

from backend.models.files import File
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestUpdateFileSizes:

    @staticmethod
    def setup_files_with_missing_size(site, count=1):
        files = []
        for _ in range(count):
            file = factories.FileFactory.create(
                site=site,
                content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
            )

            File.objects.filter(id=file.id).update(size=None)
            file.refresh_from_db()

            assert file.size is None

            files.append(file)

            if count == 1:
                return file

        return files

    @staticmethod
    def setup_file_with_missing_content(site):
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

        assert (
            "File size update process completed for all specified sites." in caplog.text
        )

    @staticmethod
    def assert_dry_run_caplog_text(caplog, site_slugs):
        for slug in site_slugs:
            assert (
                f"Starting update_file_sizes dry run for site {slug}..." in caplog.text
            )
            assert (
                f"Dry run completed for site {slug}. No changes were made."
                in caplog.text
            )

        assert (
            "Dry run process completed for all specified sites. No changes were made."
            in caplog.text
        )

    def test_update_file_sizes_no_site(self, caplog):
        call_command("update_file_sizes", site_slugs="invalid-site")
        assert "No sites with the provided slug(s) found." in caplog.text

    def test_update_file_sizes_single_site(self, caplog):
        site = factories.SiteFactory.create()
        file = self.setup_files_with_missing_size(site)

        call_command("update_file_sizes", site_slugs=site.slug)

        self.assert_caplog_text(caplog, [site.slug])

        file.refresh_from_db()

        assert file.size == file.content.size

    def test_update_file_sizes_all_sites(self, caplog):
        site1 = factories.SiteFactory.create()
        site2 = factories.SiteFactory.create()
        file1 = self.setup_files_with_missing_size(site1)
        file2 = self.setup_files_with_missing_size(site2)

        call_command("update_file_sizes")

        self.assert_caplog_text(caplog, [site1.slug, site2.slug])

        file1.refresh_from_db()
        file2.refresh_from_db()

        assert file1.size == file1.content.size
        assert file2.size == file2.content.size

    def test_timestamps(self):
        # ensure last_modified is not updated, and that system_last_modified is updated
        site = factories.SiteFactory.create()
        file = self.setup_files_with_missing_size(site)

        old_last_modified = file.last_modified

        call_command("update_file_sizes", site_slugs=site.slug)
        file.refresh_from_db()

        assert file.last_modified == old_last_modified

        assert file.system_last_modified != file.last_modified
        assert file.system_last_modified > file.last_modified

    def test_error_getting_file_size(self, caplog):
        site = factories.SiteFactory.create()
        file = self.setup_files_with_missing_size(site)

        broken_content = Mock()
        type(broken_content).size = PropertyMock(
            side_effect=Exception("Mocked exception accessing file")
        )

        with patch.object(
            File,
            "content",
            new_callable=PropertyMock,
            return_value=broken_content,
        ):
            call_command("update_file_sizes", site_slugs=site.slug)

        assert (
            f"Error accessing file size for File with ID {file.id}: Mocked exception accessing file"
            in caplog.text
        )

    def test_update_file_size_missing_content(self, caplog):
        site = factories.SiteFactory.create()
        file = self.setup_file_with_missing_content(site)
        File.objects.filter(id=file.id).update(size=None)
        file.refresh_from_db()

        call_command("update_file_sizes", site_slugs=site.slug)

        assert f"File with ID {file.id} has no content size available." in caplog.text

        file.refresh_from_db()
        assert file.size == 0

    def test_files_updated_in_batches(self, caplog):
        site = factories.SiteFactory.create()
        files = self.setup_files_with_missing_size(site, count=1200)

        call_command("update_file_sizes", site_slugs=site.slug)

        self.assert_caplog_text(caplog, [site.slug])

        for file in files:
            file.refresh_from_db()
            assert file.size == file.content.size

    def test_dry_run(self, caplog):
        site = factories.SiteFactory.create()
        file = self.setup_files_with_missing_size(site)

        call_command("update_file_sizes", site_slugs=site.slug, dry_run=True)

        assert (
            f"File with ID {file.id} on site {site.slug} would be updated with size {file.content.size}."
            in caplog.text
        )

        self.assert_dry_run_caplog_text(caplog, [site.slug])

        file.refresh_from_db()
        assert file.size is None

    def test_dry_run_missing_content(self, caplog):
        site = factories.SiteFactory.create()
        file = self.setup_file_with_missing_content(site)
        File.objects.filter(id=file.id).update(size=None)
        file.refresh_from_db()

        call_command("update_file_sizes", site_slugs=site.slug, dry_run=True)

        assert (
            f"File with ID {file.id} on site {site.slug} has no content size available. "
            f"File would be updated with size 0."
        ) in caplog.text

        self.assert_dry_run_caplog_text(caplog, [site.slug])

        file.refresh_from_db()
        assert file.size is None

    def test_dry_run_error_getting_file_size(self, caplog):
        site = factories.SiteFactory.create()
        file = self.setup_files_with_missing_size(site)

        broken_content = Mock()
        type(broken_content).size = PropertyMock(
            side_effect=Exception("Mocked exception accessing file")
        )

        with patch.object(
            File,
            "content",
            new_callable=PropertyMock,
            return_value=broken_content,
        ):
            call_command("update_file_sizes", site_slugs=site.slug, dry_run=True)

        assert (
            f"Error accessing file size for File with ID {file.id}: Mocked exception accessing file"
            in caplog.text
        )
