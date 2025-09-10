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

    def setup_method(self):
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def setup_entries_with_audio(self, speaker_name):
        person = factories.PersonFactory(name=speaker_name, site=self.site)

        related_audio = factories.AudioFactory.create(site=self.site)
        related_audio.speakers.set([person])
        related_audio.save()

        related_audio_no_speaker = factories.AudioFactory.create(site=self.site)

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

        entry_ids = DictionaryEntry.objects.all().values_list("id", flat=True)
        audio_ids = Audio.objects.filter(site=self.site).values_list("id", flat=True)
        return entry_ids, audio_ids, person

    def get_entry_csv_content(self):
        return f"id\n{self.TEST_ENTRY_UUID_1}\n{self.TEST_ENTRY_UUID_2}\n{self.TEST_ENTRY_UUID_3}\n"

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

    def test_remove_speaker_links_invalid_slug(self, caplog):
        call_command(
            "remove_speaker_links", site_slug="invalid-site", speaker_name="John Doe"
        )
        assert "Site with slug 'invalid-site' does not exist." in caplog.text

    def test_remove_speaker_links_dry_run_no_csv(self, caplog):
        entry_ids, audio_ids, _ = self.setup_entries_with_audio("John Doe")
        call_command(
            "remove_speaker_links",
            site_slug=self.site.slug,
            speaker_name="John Doe",
            dry_run=True,
        )
        assert DictionaryEntry.objects.count() == 3
        entry1 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_1)
        assert entry1.related_audio.count() == 1
        entry2 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_2)
        assert entry2.related_audio.count() == 1
        entry3 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_3)
        assert entry3.related_audio.count() == 2

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, None)
        assert "Dry run mode enabled. No changes will be made." in caplog.text
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0].id} from entry {entry_ids[0].title}."
            in caplog.text
        )
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0].id} from entry {entry_ids[2].title}."
            in caplog.text
        )

    def test_remove_speaker_links_dry_run_with_csv(self, tmp_path, caplog):
        entry_ids, audio_ids, _ = self.setup_entries_with_audio("John Doe")
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
        assert DictionaryEntry.objects.count() == 3
        entry1 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_1)
        assert entry1.related_audio.count() == 1
        entry2 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_2)
        assert entry2.related_audio.count() == 1
        entry3 = DictionaryEntry.objects.get(id=self.TEST_ENTRY_UUID_3)
        assert entry3.related_audio.count() == 2

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, str(csv_file))
        assert "Dry run mode enabled. No changes will be made." in caplog.text
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0].id} from entry {entry_ids[0].title}."
            in caplog.text
        )
        assert (
            f"[Dry Run] Would remove audio link {audio_ids[0].id} from entry {entry_ids[2].title}."
            in caplog.text
        )

    def test_remove_speaker_links_no_csv(self, tmp_path, caplog):
        entry_ids, audio_ids, person = self.setup_entries_with_audio("John Doe")
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

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, None)
        output_file = (
            tmp_path
            / f"remove_speaker_links_log_{self.site.slug}_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        )

        expected_output_csv_content = (
            "entry_id,entry_title,audio_id,audio_title,speaker_name,site\n"
            f"{self.TEST_ENTRY_UUID_1},{entry1.title},{audio_ids[0]},{audio.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_3},{entry3.title},{audio_ids[0]},{audio.title},John Doe,{self.site.slug}\n"
        )

        assert output_file.exists()
        with open(output_file) as f:
            content = f.read()
            assert content == expected_output_csv_content
        assert f"Change log written to {output_file}." in caplog.text

    def test_remove_speaker_links_with_csv(self, tmp_path, caplog):
        entry_ids, audio_ids, person = self.setup_entries_with_audio("John Doe")
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
        assert person in audio.speakers.all()

        self.assert_caplog_text(caplog, "John Doe", self.site.slug, str(csv_file))
        output_file = (
            tmp_path
            / f"remove_speaker_links_log_{self.site.slug}_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        )

        expected_output_content = (
            "entry_id,entry_title,audio_id,audio_title,speaker_name,site\n"
            f"{self.TEST_ENTRY_UUID_1},{entry1.title},{audio_ids[0]},{audio.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_2},{entry2.title},{audio_ids[1]},{Audio.objects.get(id=audio_ids[1]).title},"
            f"John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_3},{entry3.title},{audio_ids[0]},{audio.title},John Doe,{self.site.slug}\n"
            f"{self.TEST_ENTRY_UUID_3},{entry3.title},{audio_ids[1]},{Audio.objects.get(id=audio_ids[1]).title},"
            f"John Doe,{self.site.slug}\n"
        )
        assert output_file.exists()
        with open(output_file) as f:
            content = f.read()
            assert content == expected_output_content
        assert f"Change log written to {output_file}." in caplog.text
