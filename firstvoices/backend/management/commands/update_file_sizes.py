import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from backend.models import Site
from backend.models.files import File
from backend.models.media import ImageFile, VideoFile


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

    def update_file_size(self, file_instance, model):
        file_size = file_instance.content.size
        if file_size and file_instance.size != file_size:
            model.objects.filter(id=file_instance.id).update(
                size=file_size, system_last_modified=timezone.now()
            )
        elif not file_size:
            # File size not found, log a warning
            self.logger.warning(
                f"File size not found for {model.__name__} with ID {file_instance.id}"
            )

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
            files_to_update = File.objects.filter(site=site)
            image_files_to_update = ImageFile.objects.filter(site=site)
            video_files_to_update = VideoFile.objects.filter(site=site)

            with transaction.atomic():
                for file in files_to_update:
                    self.update_file_size(file_instance=file, model=File)
                for image_file in image_files_to_update:
                    self.update_file_size(file_instance=image_file, model=ImageFile)
                for video_file in video_files_to_update:
                    self.update_file_size(file_instance=video_file, model=VideoFile)

            self.logger.info(f"Completed updating file sizes for site {site.slug}.")

        self.logger.info("File size update process completed for all sites.")
