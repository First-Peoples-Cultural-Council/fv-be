import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models import Site
from backend.models.media import Audio, File, Image, Video


class Command(BaseCommand):
    help = "Convert media models with mp3 files to audio models."

    # add arguments to convert media models for a specific site
    def add_arguments(self, parser):
        parser.add_argument(
            "--site",
            dest="site_slug",
            help="Site slug of the site to convert media models for (optional)",
            default=None,
        )

    @staticmethod
    def convert_to_audio_model(model):
        with transaction.atomic():
            # convert ImageFile or VideoFile to File
            original_file = model.original
            file = File.objects.create(
                created_by=original_file.created_by,
                created=original_file.created,
                last_modified_by=original_file.last_modified_by,
                last_modified=original_file.last_modified,
                site=original_file.site,
                content=original_file.content,
                mimetype=original_file.mimetype,
                size=original_file.size,
            )

            # create Audio model
            Audio.objects.create(
                created_by=model.created_by,
                created=model.created,
                last_modified_by=model.last_modified_by,
                last_modified=model.last_modified,
                site=model.site,
                original=file,
                title=model.title,
                description=model.description,
                acknowledgement=model.acknowledgement,
                exclude_from_games=model.exclude_from_games,
                exclude_from_kids=model.exclude_from_kids,
            )

            model.delete()

    def handle(self, *args, **options):
        # Setting logger level to get all logs
        logger = logging.getLogger("convert_mp3_to_audio")
        logger.setLevel(logging.INFO)

        if options["site_slug"]:
            sites = Site.objects.filter(slug=options["site_slug"])
        else:
            sites = Site.objects.all()

        for site in sites:
            logger.info(f"Converting media models for site: {site.title}")

            # convert Image models
            image_models_to_convert = Image.objects.filter(
                site=site, original__content__endswith=".mp3"
            )
            for image_model in image_models_to_convert:
                logger.info(f"Converting Image model: {image_model.id}")
                self.convert_to_audio_model(image_model)

            # convert Video models
            video_models_to_convert = Video.objects.filter(
                site=site, original__content__endswith=".mp3"
            )
            for video_model in video_models_to_convert:
                logger.info(f"Converting Video model: {video_model.id}")
                self.convert_to_audio_model(video_model)

        logger.info("Conversion complete.")
