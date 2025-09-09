import csv
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from backend.models import Audio, DictionaryEntry, Person


class Command(BaseCommand):
    help = (
        "Removes the audio links from dictionary entries given a speaker name."
        "And/or csv file containing the uuids of the entries."
        "Speaker name is also added as a speaker to all entries that had audio removed."
    )

    logger = logging.getLogger(__name__)
    change_log = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--site",
            dest="site_slug",
            help="Site slug of the site to remove audio links from (required)",
            required=True,
        )
        parser.add_argument(
            "--speaker",
            dest="speaker_name",
            help="Name of the speaker whose links should be removed (optional)",
            required=True,
        )
        parser.add_argument(
            "--csv",
            dest="csv_file",
            help="Path to a CSV file containing the UUIDs of the dictionary entries to process (optional)",
            default=None,
        )
        parser.add_argument(
            "--typos",
            dest="typos",
            help="Provided names will be treated as typos of the speaker name (optional)",
            default=False,
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="If set, the command will only log the changes that would be made without actually making them.",
            default=False,
        )

    def remove_audio_links_by_uuid(self, uuid_list, site_slug, speaker_name, dry_run):
        """
        For each entry in the csv, marks all related audio with the provided speaker name,
        and removes the audio links from the entry.
        """
        for uuid in uuid_list:
            try:
                entry = DictionaryEntry.objects.get(uuid=uuid, site__slug=site_slug)
            except DictionaryEntry.DoesNotExist:
                self.logger.warning(
                    f"DictionaryEntry with UUID {uuid} not found in site {site_slug}."
                )
                continue

            related_audio = entry.related_audio.all()
            if related_audio.exists():
                if dry_run:
                    audio_uuids = [str(audio.uuid) for audio in related_audio]
                    self.logger.info(
                        f"[Dry Run] Would remove links to audio {audio_uuids} from entry {entry.title} "
                        f"and add speaker '{speaker_name}' to those audio models."
                    )
                else:
                    for audio in related_audio:
                        self.change_log.append(
                            {
                                "entry_id": str(entry.uuid),
                                "entry_title": entry.title,
                                "audio_id": str(audio.uuid),
                                "audio_title": audio.title,
                                "speaker_name": speaker_name,
                                "site": site_slug,
                            }
                        )
                        speaker, created = Person.objects.get_or_create(
                            name=speaker_name,
                            site=entry.site,
                            defaults={"bio": "---"},
                        )
                        audio.speakers.add(speaker)
                        audio.save(set_modified_date=False)
                        entry.related_audio.remove(audio)
                        entry.save(set_modified_date=False)

    def remove_audio_links_by_speaker(self, speaker_name, site_slug, typos, dry_run):
        site_audio = Audio.objects.filter(site__slug=site_slug)
        speakers_to_check = [speaker_name]
        if typos:
            speakers_to_check = speakers_to_check + typos.split(",")

        for name in speakers_to_check:
            name = name.strip()
            audio_to_unlink = site_audio.filter(speakers__name__iexact=name).distinct()
            for audio in audio_to_unlink:
                related_entries = DictionaryEntry.objects.filter(
                    related_audio=audio, site__slug=site_slug
                )
                for entry in related_entries:
                    if dry_run:
                        self.logger.info(
                            f"[Dry Run] Would remove audio link {audio.uuid} from entry {entry.title}."
                        )
                    else:
                        self.change_log.append(
                            {
                                "entry_id": str(entry.uuid),
                                "entry_title": entry.title,
                                "audio_id": str(audio.uuid),
                                "audio_title": audio.title,
                                "speaker_name": speaker_name,
                                "site": site_slug,
                            }
                        )
                        entry.related_audio.remove(audio)
                        entry.save(set_modified_date=False)

    def handle(self, *args, **options):

        site_slug = options["site_slug"]
        speaker_name = options["speaker_name"].strip()
        csv_file = options["csv_file"]
        typos = options["typos"]
        dry_run = options["dry_run"]

        self.logger.info(
            f"Starting to remove speaker links for speaker '{speaker_name}' in site '{site_slug}'."
        )
        if dry_run:
            self.logger.info("Dry run mode enabled. No changes will be made.")

        if csv_file:
            self.logger.info(f"Processing entries from CSV file: {csv_file}")
            try:
                with open(csv_file) as f:
                    uuid_list = []
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row:
                            uuid_list.append(row["id"].strip())

                self.remove_audio_links_by_uuid(
                    uuid_list, site_slug, speaker_name, dry_run
                )
            except FileNotFoundError:
                self.logger.warning(f"Error: CSV file '{csv_file}' not found.")
                return
            except Exception as e:
                self.logger.warning(f"Error reading CSV file '{csv_file}': {e}")
                return

        if speaker_name:
            self.logger.info(f"Processing entries for speaker: {speaker_name}")
            self.remove_audio_links_by_speaker(speaker_name, site_slug, typos, dry_run)
        self.logger.info("Finished removing speaker links.")

        if not dry_run and self.change_log:
            log_file = f"remove_speaker_links_log_{site_slug}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(log_file, "w", newline="") as csvfile:
                fieldnames = [
                    "entry_id",
                    "entry_title",
                    "audio_id",
                    "audio_title",
                    "speaker_name",
                    "site",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for change in self.change_log:
                    writer.writerow(change)
            self.logger.info(f"Change log written to {log_file}.")
