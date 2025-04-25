import logging
import re
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from PIL import Image as PILImage
from pillow_heif import register_heif_opener

from backend.models import Site
from backend.models.media import Image, ImageFile


class Command(BaseCommand):
    help = "Converts heic files within image models to jpeg or png files"
    HEIC_EXTENSION = ".heic"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            dest="site_slugs",
            help="Site slugs of the sites to convert heic content for, separated by comma (optional)",
            default=None,
        )

    @staticmethod
    def is_transparent(image: ImageFile) -> bool:
        """
        Check if the image has transparency.
        """
        img = PILImage.open(image.content.file)
        return img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        )

    def convert_heic_to_png(self, image: ImageFile) -> ImageFile:
        # get original image content
        original_image = image.content
        img = PILImage.open(original_image.file)

        # convert to png
        img = img.convert("RGBA")
        output_image = BytesIO()
        img.save(output_image, format="PNG", optimize=True)
        output_image.seek(0)

        # Create a new ImageField instance
        content = InMemoryUploadedFile(
            file=output_image,
            field_name="ImageField",
            name=re.sub(
                self.HEIC_EXTENSION, ".png", original_image.name, flags=re.IGNORECASE
            ),
            content_type="image/png",
            size=output_image.getbuffer().nbytes,
            charset=None,
        )

        # Create a new ImageFile instance
        converted_image = ImageFile(
            content=content,
            site=image.site,
            created_by=image.created_by,
            last_modified_by=image.last_modified_by,
        )
        converted_image.save()

        return converted_image

    def convert_heic_to_jpeg(self, image: ImageFile) -> ImageFile:
        # get original image content
        original_image = image.content
        img = PILImage.open(original_image.file)

        # convert to jpeg
        img = img.convert("RGB")
        output_image = BytesIO()
        img.save(output_image, format="JPEG", optimize=True)
        output_image.seek(0)

        # Create a new ImageField instance
        content = InMemoryUploadedFile(
            file=output_image,
            field_name="ImageField",
            name=re.sub(
                self.HEIC_EXTENSION, ".jpg", original_image.name, flags=re.IGNORECASE
            ),
            content_type="image/jpeg",
            size=output_image.getbuffer().nbytes,
            charset=None,
        )

        # Create a new ImageFile instance
        converted_image = ImageFile(
            content=content,
            site=image.site,
            created_by=image.created_by,
            last_modified_by=image.last_modified_by,
        )
        converted_image.save()

        return converted_image

    def convert_images(self, images, logger):
        for image in images:
            heic_image = image.original

            try:
                if self.is_transparent(heic_image):
                    logger.debug(f"Converting image {image.id} to png...")
                    converted_image = self.convert_heic_to_png(heic_image)
                else:
                    logger.debug(f"Converting image {image.id} to jpeg...")
                    converted_image = self.convert_heic_to_jpeg(heic_image)

                with transaction.atomic():
                    image.original = converted_image
                    image.save(set_modified_date=False)

                    transaction.on_commit(lambda img=heic_image: img.delete())

            except Exception as e:
                logger.error(
                    f"Error converting HEIC image {image.id} for site {image.site.slug}: {e}"
                )
                continue

    def log_orphaned_heic_images(self, site, logger):
        orphaned_images = ImageFile.objects.filter(
            Q(mimetype__iexact="image/heic")
            | Q(content__iendswith=self.HEIC_EXTENSION),
            site=site,
        )

        if orphaned_images:
            logger.info(
                f"The following orphaned HEIC images were found for site {site.slug}, and not converted:\n"
                + "\n".join(
                    f"- {image.id}: {image.content.name}" for image in orphaned_images
                )
            )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

        # Activate pillow_heif plugin
        register_heif_opener(thumbnails=False)

        if options.get("site_slugs"):
            site_slug_list = [
                s.strip() for s in options.get("site_slugs", "").split(",")
            ]
            sites = Site.objects.filter(slug__in=site_slug_list)
            if not sites:
                logger.warning("No sites with the provided slug(s) found.")
                return
        else:
            sites = Site.objects.all()

        logger.info(f"Converting HEIC files to JPEG/PNG for {len(sites)} sites.")

        for site in sites:
            logger.debug(f"Converting heic content to jpeg/png for site {site.slug}...")
            images = Image.objects.filter(
                Q(original__mimetype__iexact="image/heic")
                | Q(original__content__iendswith=self.HEIC_EXTENSION),
                site=site,
            )

            if not images:
                logger.info(f"No HEIC images found for site {site.slug}.")
                self.log_orphaned_heic_images(site, logger)
                continue

            self.convert_images(images, logger)
            self.log_orphaned_heic_images(site, logger)

        logger.info("HEIC to JPEG/PNG conversion completed.")
