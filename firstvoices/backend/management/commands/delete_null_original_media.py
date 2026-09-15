import csv
import logging
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from backend.models.media import Audio, Document, Image, Video

MEDIA_MODELS = [Audio, Document, Image, Video]


class Command(BaseCommand):
    help = (
        "Deletes media records (Audio, Document, Image, Video) that have no "
        "original file. Run before applying the migration that makes the "
        "'original' field non-nullable."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.change_log = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            dest="output_dir",
            help="Directory to save the change log CSV file (default is current directory).",
            default=".",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="If set, the command will only log the changes that would be made without actually making them.",
            default=False,
        )

    def validate_output_dir(self, output_dir):
        output_dir = os.path.expandvars(os.path.expanduser(output_dir))
        if not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK):
            self.logger.error(
                f"Output directory '{output_dir}' does not exist or is not writeable."
            )
            return None
        return output_dir

    def output_change_log(self, output_dir):
        log_filename = f"delete_null_original_media_log_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        log_file = os.path.join(output_dir, log_filename)
        with open(log_file, "w", newline="") as csvfile:
            fieldnames = ["model", "id", "title", "site"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for change in self.change_log:
                writer.writerow(change)
        self.logger.info(f"Change log written to {log_file}.")

    def handle(self, *args, **options):
        output_dir = options["output_dir"]
        dry_run = options["dry_run"]
        output_dir = self.validate_output_dir(output_dir)
        if output_dir is None:
            return
        self.logger.info("Starting to delete media with null original files.")
        if dry_run:
            self.logger.info("Dry run mode enabled. No changes will be made.")
        with transaction.atomic():
            for model in MEDIA_MODELS:
                queryset = model.objects.filter(original__isnull=True)
                count = queryset.count()
                if not count:
                    continue
                if dry_run:
                    ids = [str(pk) for pk in queryset.values_list("id", flat=True)]
                    self.logger.info(
                        f"[Dry Run] Would delete {count} {model.__name__} "
                        f"records with null original."
                    )
                    self.logger.info(f"{model.__name__}s: {ids}")
                    continue
                self.logger.info(
                    f"Deleting {count} {model.__name__} record(s) with null original."
                )
                for instance in queryset:
                    self.change_log.append(
                        {
                            "model": model.__name__,
                            "id": str(instance.id),
                            "title": instance.title,
                            "site": instance.site.slug,
                        }
                    )
                    instance.delete()
        if not dry_run and self.change_log:
            self.output_change_log(output_dir)
        self.logger.info("Finished deleting media with null original files.")
