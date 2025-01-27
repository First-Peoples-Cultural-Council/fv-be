import logging

from django.core.management.base import BaseCommand

from backend.models import Site


class Command(BaseCommand):
    help = "Copy a site from a source slug to a target slug."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            dest="source_slug",
            help="Site slug of the site to copy from.",
            required=True,
        )
        parser.add_argument(
            "--target",
            dest="target_slug",
            help="Site slug of the site to copy to.",
            required=True,
        )
        parser.add_argument(
            "--title",
            dest="title",
            help="Title of the newly created site.",
            required=True,
        )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

        source_slug = options["source_slug"]
        target_slug = options["target_slug"]
        # title = options["title"]

        if Site.objects.filter(slug=target_slug).exists():
            logger.error(f"Site with slug {target_slug} already exists.")
            return

        logger.info(f"Copying site {source_slug} to {target_slug}...")

        # source_site = Site.objects.get(slug=source_slug)

        # TODO: Copy the site here
