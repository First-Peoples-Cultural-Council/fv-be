import csv
import logging
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from backend.models import DictionaryEntry, Site, Song, Story
from backend.models.files import File
from backend.models.media import Audio, Document, Image, Video


class Command(BaseCommand):
    help = "Export site-level content statistics to a CSV file."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument(
            "--site",
            dest="site_slug",
            help="Site slug of a specific site to export. If unspecified, exports all sites.",
            required=False,
        )
        parser.add_argument(
            "--output",
            dest="output_path",
            help="Optional output file path. Defaults to a timestamped CSV in the current directory.",
            required=False,
        )

    def handle(self, *args, **options):
        site_slug = options.get("site_slug")
        output_path = options.get("output_path")

        if output_path:
            output_file = Path(output_path)
            if not output_file.parent.exists():
                raise CommandError(
                    f"Output directory does not exist: {output_file.parent}"
                )
        else:
            now = datetime.now()
            timestamp = now.strftime("%Y_%m_%d_%H_%M")
            filename = f"site_stats_{timestamp}.csv"
            output_file = Path(Path.cwd() / filename)

        if site_slug:
            sites = Site.objects.filter(slug=site_slug)
            if len(sites) == 0:
                raise CommandError(f"Site with slug '{site_slug}' does not exist.")
        else:
            sites = list(Site.objects.all())

        if not sites:
            raise CommandError("No sites found to export.")

        self.logger.info(f"Exporting stats for {len(sites)} site(s).")
        self.logger.info(f"Output file: {output_file}")

        totals = {
            "words": 0,
            "phrases": 0,
            "songs": 0,
            "stories": 0,
            "images": 0,
            "videos": 0,
            "audios": 0,
            "documents": 0,
            "files": 0,
        }

        with output_file.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(
                [
                    "site_name",
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
            )

            for index, site in enumerate(sites):
                self.logger.info(
                    f"Processing site {site.slug} ({index+1}/{len(sites)})"
                )

                words = DictionaryEntry.objects.filter(site=site, type="word").count()
                phrases = DictionaryEntry.objects.filter(
                    site=site, type="phrase"
                ).count()
                songs = Song.objects.filter(site=site).count()
                stories = Story.objects.filter(site=site).count()
                images = Image.objects.filter(site=site).count()
                videos = Video.objects.filter(site=site).count()
                audios = Audio.objects.filter(site=site).count()
                documents = Document.objects.filter(site=site).count()
                files = File.objects.filter(site=site).count()

                # Log progress
                self.logger.info(
                    f"Counts: words={words}, phrases={phrases}, songs={songs}, "
                    f"stories={stories}, images={images}, videos={videos}, "
                    f"audios={audios}, documents={documents}, files={files}"
                )

                totals["words"] += words
                totals["phrases"] += phrases
                totals["songs"] += songs
                totals["stories"] += stories
                totals["images"] += images
                totals["videos"] += videos
                totals["audios"] += audios
                totals["documents"] += documents
                totals["files"] += files

                writer.writerow(
                    [
                        getattr(site, "title", ""),
                        words,
                        phrases,
                        songs,
                        stories,
                        images,
                        videos,
                        audios,
                        documents,
                        files,
                    ]
                )

            writer.writerow([])

            writer.writerow(
                [
                    "TOTAL",
                    totals["words"],
                    totals["phrases"],
                    totals["songs"],
                    totals["stories"],
                    totals["images"],
                    totals["videos"],
                    totals["audios"],
                    totals["documents"],
                    totals["files"],
                ]
            )

        self.logger.info("Export completed successfully.")
        self.logger.info(f"File saved as: {output_file}")
