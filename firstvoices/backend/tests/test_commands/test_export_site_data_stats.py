import csv
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command

from backend.tests import factories


@pytest.mark.django_db
class TestExportSiteStats:
    COMMAND = "export_site_data_stats"

    def test_invalid_site_slug_raises_error(self):
        with pytest.raises(CommandError) as e:
            call_command(self.COMMAND, site_slug="does_not_exist")

        assert "does not exist" in str(e.value)

    def test_invalid_output_directory_raises_error(self, tmp_path):
        invalid_path = tmp_path / "abcxyz" / "file.csv"

        with pytest.raises(CommandError) as e:
            call_command(self.COMMAND, output_path=str(invalid_path))

        assert "Output directory does not exist" in str(e.value)

    def test_default_output_file_created(self, tmp_path):
        factories.SiteFactory.create()

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            call_command(self.COMMAND)

        csv_files = list(tmp_path.glob("site_stats_*.csv"))
        assert len(csv_files) == 1
        assert "site_stats" in csv_files[0].name

    def test_custom_output_path(self, tmp_path):
        factories.SiteFactory.create()
        output_file = tmp_path / "custom.csv"

        call_command(self.COMMAND, output_path=str(output_file))

        assert output_file.exists()

    def test_single_site_export_counts(self, tmp_path):
        site = factories.SiteFactory()
        factories.DictionaryEntryFactory(site=site, type="word")
        factories.DictionaryEntryFactory(site=site, type="phrase")
        factories.SongFactory(site=site)
        factories.StoryFactory(site=site)
        factories.ImageFactory(site=site)
        factories.VideoFactory(site=site)
        factories.AudioFactory(site=site)
        factories.DocumentFactory(site=site)
        factories.FileFactory(site=site)

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            call_command(self.COMMAND, site_slug=site.slug)

        csv_files = list(tmp_path.glob("site_stats_*.csv"))
        assert len(csv_files) == 1
        csv_file = csv_files[0]

        with csv_file.open() as f:
            rows = list(csv.reader(f))

        assert len(rows) == 4

        header = rows[0]
        data_row = rows[1]
        totals_row = rows[3]

        assert header == [
            "site_slug",
            "words",
            "phrases",
            "songs",
            "stories",
            "images",
            "videos",
            "audios",
            "documents",
            "files",
        ]

        assert data_row[0] == site.slug
        assert data_row[1:] == totals_row[1:]

    def test_multiple_sites_export(self, tmp_path):
        site1 = factories.SiteFactory(title="Site1")
        site2 = factories.SiteFactory(title="Site2")

        # Add one entry to each site
        factories.DictionaryEntryFactory(site=site1, type="word")
        factories.DictionaryEntryFactory(site=site2, type="word")

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            call_command(self.COMMAND)

        csv_files = list(tmp_path.glob("site_stats_*.csv"))
        assert len(csv_files) == 1
        csv_file = csv_files[0]

        with csv_file.open() as f:
            rows = list(csv.reader(f))

        assert len(rows) == 5

        totals_row = rows[-1]
        assert totals_row[1] == "2"

    def test_logging_progress(self, tmp_path, caplog):
        site = factories.SiteFactory()

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            call_command(self.COMMAND)

        assert f"Processing site {site.slug}" in caplog.text
        assert "Counts:" in caplog.text
