from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from backend.models import Audio, DictionaryEntry
from backend.models.constants import Visibility
from backend.tests import factories


@pytest.mark.django_db
class TestRemoveSpeakerLinks:
    TEST_ENTRY_UUID_1 = "c36275d4-ba71-4efc-8bbe-c1f91d0bdeff"
    TEST_ENTRY_UUID_2 = "4a2e3113-5c7e-44df-9e6a-cc11a10f5fa0"
    TEST_ENTRY_UUID_3 = "dfcaae4d-f01f-4fc5-b0ca-7366e7fdf8b9"

    TEST_AUDIO_UUID_1 = "135740ac-b271-46dd-8d54-5f4df42f519b"
    TEST_AUDIO_UUID_2 = "d47a1375-ff3e-4d2b-9275-168cefc1e92d"
    TEST_AUDIO_UUID_3 = "0e952fbf-b122-4feb-a91c-11e302e36502"

    def setup_method(self):
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def setup_entries_with_audio(self, speaker_name):
        person = factories.PersonFactory(name=speaker_name, site=self.site)

        related_audio = factories.AudioFactory.create(
            site=self.site, id=self.TEST_AUDIO_UUID_1
        )
        related_audio.speakers.set([person])
        related_audio.save()

        related_audio_no_speaker = factories.AudioFactory.create(
            site=self.site, id=self.TEST_AUDIO_UUID_2
        )

        entry1 = factories.DictionaryEntryFactory.create(
            id=self.TEST_ENTRY_UUID_1,
            site=self.site,
        )
        entry1.related_audio.set([related_audio])
        entry1.save()

        entry2 = factories.DictionaryEntryFactory.create(
            id=self.TEST_ENTRY_UUID_2,
            site=self.site,
        )
        entry2.related_audio.set([related_audio_no_speaker])
        entry2.save()

        entry3 = factories.DictionaryEntryFactory.create(
            id=self.TEST_ENTRY_UUID_3,
            site=self.site,
        )
        entry3.related_audio.set([related_audio, related_audio_no_speaker])
        entry3.save()

        return [related_audio.id, related_audio_no_speaker.id], person

    def setup_typo_audio(self, typo_name):
        typo_person = factories.PersonFactory(name=typo_name, site=self.site)
        typo_audio = factories.AudioFactory.create(
            site=self.site, id=self.TEST_AUDIO_UUID_3
        )
        typo_audio.speakers.set([typo_person])
        typo_audio.save()
        return typo_audio

    def get_entry_csv_content(self):
        return f"id\n{self.TEST_ENTRY_UUID_1}\n{self.TEST_ENTRY_UUID_2}\n{self.TEST_ENTRY_UUID_3}\n"

    def assert_entries_unchanged(self):
        assert DictionaryEntry.objects.count() == 3
        assert Audio.objects.count() == 2
        entry1 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_1)
        assert entry1.related_audio.count() == 1
        entry2 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_2)
        assert entry2.related_audio.count() == 1
        entry3 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_3)
        assert entry3.related_audio.count() == 2
        return [entry1, entry2, entry3]

    @staticmethod
    def assert_caplog_text(caplog, speaker_name, site_slug, csv_file):
        assert (
            f"Starting to remove speaker links for speaker '{speaker_name}' in site '{site_slug}'."
            in caplog.text
        )
        assert f"Processing entries for speaker: {speaker_name}" in caplog.text
        assert "Finished removing speaker links." in caplog.text
        if csv_file:
            assert f"Processing entries from CSV file: {csv_file}" in caplog.text

    def test_remove_speaker_links_invalid_output_dir(self, caplog):
        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            output_dir="/invalid/dir",
        )
        assert (
            "Output directory '/invalid/dir' does not exist or is not writeable."
            in caplog.text
        )

    def test_remove_speaker_links_invalid_slug(self, caplog):
        call_command(
            "remove_speaker_links", site_slug="invalid-site", speaker_name="John Doe"
        )
        assert "Site with slug 'invalid-site' does not exist." in caplog.text

    def test_remove_speaker_links_invalid_csv(self, tmp_path, caplog):
        csv_file = tmp_path / "non_existent_file.csv"
        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            csv_file=str(csv_file),
        )
        assert f"Error: CSV file '{csv_file}' not found." in caplog.text

    def test_remove_speaker_links_csv_read_error(self, tmp_path, caplog):
        csv_file = tmp_path / "invalid_format.csv"
        with open(csv_file, "w") as f:
            f.write("invalid_column\n123\n456\n")
        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            csv_file=str(csv_file),
        )
        assert f"Error reading CSV file '{csv_file}':" in caplog.text

    def test_remove_speaker_links_missing_entries_in_csv(self, tmp_path, caplog):
        csv_file = tmp_path / "test_speaker_links.csv"
        with open(csv_file, "w") as f:
            f.write(self.get_entry_csv_content())

        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            csv_file=str(csv_file),
        )
        assert DictionaryEntry.objects.count() == 0
        assert (
            f"DictionaryEntry with ID {self.TEST_ENTRY_UUID_1} not found in site {self.site.slug}."
            in caplog.text
        )
        assert (
            f"DictionaryEntry with ID {self.TEST_ENTRY_UUID_2} not found in site {self.site.slug}."
            in caplog.text
        )
        assert (
            f"DictionaryEntry with ID {self.TEST_ENTRY_UUID_3} not found in site {self.site.slug}."
            in caplog.text
        )

    def test_remove_speaker_links_dry_run_no_csv(self, caplog):
        audio_ids, _ = self.setup_entries_with_audio("John Doe")
        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            dry_run=True,
        )
        entries = self.assert_entries_unchanged()

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, None)
        assert "Dry run mode enabled. No changes will be made." in caplog.text
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0]} from entry {entries[0].title}."
            in caplog.text
        )
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0]} from entry {entries[2].title}."
            in caplog.text
        )

    def test_remove_speaker_links_dry_run_with_csv(self, tmp_path, caplog):
        audio_ids, _ = self.setup_entries_with_audio("John Doe")
        csv_file = tmp_path / "test_speaker_links.csv"
        with open(csv_file, "w") as f:
            f.write(self.get_entry_csv_content())

        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            csv_file=str(csv_file),
            dry_run=True,
        )
        entries = self.assert_entries_unchanged()

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, str(csv_file))
        assert "Dry run mode enabled. No changes will be made." in caplog.text

        assert (
            f"[Dry Run] Would remove links to audio {self.TEST_AUDIO_UUID_1} from entry {entries[0].title} "
            f"and add speaker 'John Doe' to affected audio instances."
        ) in caplog.text
        assert (
            f"[Dry Run] Would remove links to audio {self.TEST_AUDIO_UUID_2} from entry {entries[1].title} "
            f"and add speaker 'John Doe' to affected audio instances."
        )
        assert (
            f"[Dry Run] Would remove links to audio {self.TEST_AUDIO_UUID_1}, {self.TEST_AUDIO_UUID_2} "
            f"from entry {entries[2].title} and add speaker 'John Doe' to affected audio instances."
        )

        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0]} from entry {entries[0].title}."
            in caplog.text
        )
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0]} from entry {entries[2].title}."
            in caplog.text
        )

    def test_remove_speaker_links_no_csv(self, tmp_path, caplog):
        audio_ids, person = self.setup_entries_with_audio("John Doe")
        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            output_dir=str(tmp_path),
            dry_run=False,
        )
        assert DictionaryEntry.objects.count() == 3
        entry1 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_1)
        assert entry1.related_audio.count() == 0
        entry2 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_2)
        assert entry2.related_audio.count() == 1
        entry3 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_3)
        assert entry3.related_audio.count() == 1

        audio = Audio.objects.get(id=audio_ids[0])
        assert person in audio.speakers.all()

        audio2 = Audio.objects.get(id=audio_ids[1])
        assert person not in audio2.speakers.all()

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, None)
        output_file = (
            tmp_path
            / f"remove_speaker_links_log_{self.site.slug}_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        )

        expected_output_csv_content = (
            "entry_id,entry_title,audio_id,audio_title,speaker_name,site\n"
            f"{self.TEST_ENTRY_UUID_1},{entry1.title},{audio.id},{audio.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_3},{entry3.title},{audio.id},{audio.title},John Doe,{self.site.slug}\n"
        )

        assert output_file.exists()
        with open(output_file) as f:
            content = f.read()
            assert content == expected_output_csv_content
        assert f"Change log written to {output_file}." in caplog.text

    def test_remove_speaker_links_with_csv(self, tmp_path, caplog):
        audio_ids, person = self.setup_entries_with_audio("John Doe")
        csv_file = tmp_path / "test_speaker_links.csv"
        with open(csv_file, "w") as f:
            f.write(self.get_entry_csv_content())

        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            output_dir=str(tmp_path),
            csv_file=str(csv_file),
            dry_run=False,
        )
        assert DictionaryEntry.objects.count() == 3
        entry1 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_1)
        assert entry1.related_audio.count() == 0
        entry2 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_2)
        assert entry2.related_audio.count() == 0
        entry3 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_3)
        assert entry3.related_audio.count() == 0

        audio = Audio.objects.get(id=audio_ids[0])
        audio2 = Audio.objects.get(id=audio_ids[1])
        assert person in audio.speakers.all()
        assert person in audio2.speakers.all()

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, str(csv_file))
        output_file = (
            tmp_path
            / f"remove_speaker_links_log_{self.site.slug}_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        )

        expected_output_content = (
            "entry_id,entry_title,audio_id,audio_title,speaker_name,site\n"
            f"{self.TEST_ENTRY_UUID_1},{entry1.title},{audio.id},{audio.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_2},{entry2.title},{audio2.id},{audio2.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_3},{entry3.title},{audio.id},{audio.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_3},{entry3.title},{audio2.id},{audio2.title},John Doe,{self.site.slug}\n"
        )
        assert output_file.exists()
        with open(output_file) as f:
            content = f.read()
            assert content == expected_output_content
        assert f"Change log written to {output_file}." in caplog.text

    def test_remove_speaker_links_typo_dry_run(self, caplog):
        audio_ids, _ = self.setup_entries_with_audio("John Doe")

        typo_audio = self.setup_typo_audio("Jhon Doe")

        entry1 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_1)
        entry1.related_audio.add(typo_audio)
        entry1.save()

        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            typos="Jhon Doe, Jon Doe",
            dry_run=True,
        )

        assert DictionaryEntry.objects.count() == 3
        assert entry1.related_audio.count() == 2
        entry2 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_2)
        assert entry2.related_audio.count() == 1
        entry3 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_3)
        assert entry3.related_audio.count() == 2

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, None)
        assert "Dry run mode enabled. No changes will be made." in caplog.text
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0]} from entry {entry1.title}."
            in caplog.text
        )
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0]} from entry {entry3.title}."
            in caplog.text
        )
        assert (
            f"[Dry Run] Would remove audio link {typo_audio.id} from entry {entry1.title}."
            in caplog.text
        )

    def test_remove_speaker_links_typo(self, tmp_path, caplog):
        audio_ids, person = self.setup_entries_with_audio("John Doe")

        typo_audio = self.setup_typo_audio("Jhon Doe")

        entry1 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_1)
        entry1.related_audio.add(typo_audio)
        entry1.save()

        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            typos="Jhon Doe, Jon Doe",
            output_dir=str(tmp_path),
            dry_run=False,
        )

        assert DictionaryEntry.objects.count() == 3
        assert entry1.related_audio.count() == 0
        entry2 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_2)
        assert entry2.related_audio.count() == 1
        entry3 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_3)
        assert entry3.related_audio.count() == 1

        audio = Audio.objects.get(id=audio_ids[0])
        assert person in audio.speakers.all()

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, None)
        output_file = (
            tmp_path
            / f"remove_speaker_links_log_{self.site.slug}_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        )

        expected_output_content = (
            "entry_id,entry_title,audio_id,audio_title,speaker_name,site\n"
            f"{self.TEST_ENTRY_UUID_1},{entry1.title},{audio_ids[0]},{audio.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_3},{entry3.title},{audio_ids[0]},{audio.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_1},{entry1.title},{typo_audio.id},{typo_audio.title},John Doe,{self.site.slug}\n"
        )
        assert output_file.exists()
        with open(output_file) as f:
            content = f.read()
            assert content == expected_output_content
        assert f"Change log written to {output_file}." in caplog.text

    def test_rollback_if_error(self, tmp_path):
        self.setup_entries_with_audio("John Doe")
        csv_file = tmp_path / "test_speaker_links.csv"
        with open(csv_file, "w") as f:
            f.write(self.get_entry_csv_content())

        with patch.object(
            DictionaryEntry, "save", side_effect=Exception("Mocked exception")
        ):
            call_command(
                "remove_speaker_links",
                site_slug=self.site.slug,
                speaker_name="John Doe",
                output_dir=str(tmp_path),
                csv_file=str(csv_file),
                dry_run=False,
            )

        self.assert_entries_unchanged()
