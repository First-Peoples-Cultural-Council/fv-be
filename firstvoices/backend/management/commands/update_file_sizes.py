import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from backend.models import Site
from backend.models.files import File

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "Update file sizes for all files in the database."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            dest="site_slugs",
            help="Site slugs of the sites to update file sizes for, separated by comma (optional)",
            default=None,
        )

    def bulk_update_files(self, batch, files_to_update):
        for file in files_to_update:
            try:
                content_size = file.content.size
            except Exception as e:
                self.logger.warning(
                    f"Error accessing file size for File with ID {file.id}: {e}"
                )
                continue

            if content_size:
                file.size = content_size
                file.system_last_modified = timezone.now()
                batch.append(file)
            else:
                self.logger.warning(
                    f"File with ID {file.id} has no content size available."
                )
                file.size = 0
                file.system_last_modified = timezone.now()
                batch.append(file)

            if len(batch) >= BATCH_SIZE:
                File.objects.bulk_update(batch, ["size", "system_last_modified"])
                batch.clear()

        if batch:
            File.objects.bulk_update(batch, ["size", "system_last_modified"])

    def handle(self, *args, **options):

        if options.get("site_slugs"):
            site_slug_list = [
                s.strip() for s in options.get("site_slugs", "").split(",")
            ]
            sites = Site.objects.filter(slug__in=site_slug_list)
            if not sites:
                self.logger.warning("No sites with the provided slug(s) found.")
                return
        else:
            sites = Site.objects.all()

        for site in sites:
            self.logger.info(f"Updating file sizes for media files in {site.slug}...")
            files_to_update = (
                File.objects.filter(site=site, size__isnull=True)
                .only("id", "content", "size", "system_last_modified")
                .iterator(chunk_size=1000)
            )

            batch = []
            self.bulk_update_files(batch, files_to_update)

            self.logger.info(f"Completed updating file sizes for site {site.slug}.")

        self.logger.info("File size update process completed for all sites.")
