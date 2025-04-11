import logging
import sys
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image as PILImage
from pillow_heif import register_heif_opener

from backend.models import Site
from backend.models.media import Image, ImageFile


class Command(BaseCommand):
    help = "Converts heic files within image models to png files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            dest="site_slugs",
            help="Site slugs of the sites to convert heic content for, separated by comma (optional)",
            default=None,
        )

    @staticmethod
    def convert_heic_to_png(image: ImageFile) -> ImageFile:
        # Activate pillow_heif plugin
        register_heif_opener(thumbnails=False)

        # get original image content
        original_image = image.content
        img = PILImage.open(original_image.file)

        # check for transparency
        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        # convert to png
        output_image = BytesIO()
        img.save(output_image, format="PNG", optimize=True)
        output_image.seek(0)

        # Create a new ImageField instance
        content = InMemoryUploadedFile(
            file=output_image,
            field_name="ImageField",
            name=original_image.name.replace(".heic", ".png"),
            content_type="image/png",
            size=sys.getsizeof(output_image),
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

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

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

        logger.info(f"Converting HEIC files to PNG for {len(sites)} sites.")

        for site in sites:
            logger.debug(f"Converting heic content to png for site {site.slug}...")
            images = Image.objects.filter(
                site=site, original__content__endswith=".heic"
            )

            if not images:
                logger.warning(f"No HEIC images found for site {site.slug}.")
                continue

            for image in images:
                logger.debug(f"Converting image {image.id} to png...")
                heic_image = image.original

                with transaction.atomic():
                    converted_image = self.convert_heic_to_png(heic_image)
                    image.original = converted_image
                    image.save(set_modified_date=False)

                    transaction.on_commit(lambda: heic_image.delete())

        logger.info("HEIC to PNG conversion completed.")
