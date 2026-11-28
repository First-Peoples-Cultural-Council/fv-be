import csv
import logging
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from backend.models import Category, Site

PHRASES_SUFFIX = " (phrases)"


class Command(BaseCommand):
    help = (
        "Merges 'Category (phrases)' categories into the matching category on a site, "
        "then removes extra spaces from category titles."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.change_log = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--site",
            dest="site_slug",
            help="Site slug of the site to merge categories for (required)",
            required=True,
        )
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

    def merge_phrases_categories(self, site, dry_run):
        categories = Category.objects.filter(site=site)
        targets = {
            c.title.strip(): c
            for c in categories
            if not c.title.endswith(PHRASES_SUFFIX)
        }
        merged = 0

        for source in categories.filter(title__endswith=PHRASES_SUFFIX):
            target = targets.get(source.title.removesuffix(PHRASES_SUFFIX).strip())
            if not target:
                continue

            links = source.dictionaryentrycategory_set.all()
            self.change_log.append(
                {
                    "action": "merge",
                    "category_id": str(source.id),
                    "title": source.title,
                    "target_id": str(target.id),
                    "new_title": target.title,
                    "entries": links.count(),
                }
            )
            merged += 1

            if dry_run:
                self.logger.info(
                    f"[Dry Run] Would merge category {source.id} into {target.id}."
                )
                continue

            if source.description and not target.description:
                target.description = source.description
                target.save(set_modified_date=False)

            for link in links:
                link.category = target
                link.save(set_modified_date=False)

            source.delete()

        self.logger.info(f"Merged {merged} categories for site '{site.slug}'.")

    def clean_up_titles(self, site, dry_run):
        cleaned = 0

        for category in Category.objects.filter(site=site):
            title = " ".join(category.title.split())
            if title == category.title:
                continue

            self.change_log.append(
                {
                    "action": "clean_up",
                    "category_id": str(category.id),
                    "title": category.title,
                    "target_id": "",
                    "new_title": title,
                    "entries": "",
                }
            )
            cleaned += 1

            if dry_run:
                self.logger.info(
                    f"[Dry Run] Would clean up the title of category {category.id}."
                )
                continue

            category.title = title
            category.save(set_modified_date=False)

        self.logger.info(
            f"Cleaned up {cleaned} category titles for site '{site.slug}'."
        )

    def validate_output_dir(self, output_dir):
        output_dir = os.path.expandvars(os.path.expanduser(output_dir))
        if not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK):
            self.logger.error(
                f"Output directory '{output_dir}' does not exist or is not writeable."
            )
            return None
        return output_dir

    def output_change_log(self, site_slug, output_dir, dry_run):
        prefix = "dry_run_" if dry_run else ""
        log_filename = (
            f"{prefix}merge_duplicate_categories_log_{site_slug}_"
            f"{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        log_file = os.path.join(output_dir, log_filename)
        with open(log_file, "w", newline="", encoding="utf-8-sig") as csvfile:
            fieldnames = [
                "action",
                "category_id",
                "title",
                "target_id",
                "new_title",
                "entries",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for change in self.change_log:
                writer.writerow(change)
        self.logger.info(f"Change log written to {log_file}.")

    def handle(self, *args, **options):
        site_slug = options["site_slug"]
        output_dir = options["output_dir"]
        dry_run = options["dry_run"]

        output_dir = self.validate_output_dir(output_dir)
        if output_dir is None:
            return

        site = Site.objects.filter(slug=site_slug).first()
        if not site:
            self.logger.warning(f"Site with slug '{site_slug}' does not exist.")
            return

        self.logger.info(
            f"Starting to merge duplicate categories for site '{site_slug}'."
        )
        if dry_run:
            self.logger.info("Dry run mode enabled. No changes will be made.")

        with transaction.atomic():
            self.merge_phrases_categories(site, dry_run)
            self.clean_up_titles(site, dry_run)

        if self.change_log:
            self.output_change_log(site_slug, output_dir, dry_run)
        self.logger.info(
            f"Finished merging duplicate categories for site '{site_slug}'."
        )
