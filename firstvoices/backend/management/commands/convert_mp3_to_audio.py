import logging

from django.core.files.uploadedfile import UploadedFile
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
    def convert_model_related_links(original_model, audio_model):
        related_models = [
            original_model.character_set,
            original_model.dictionaryentry_set,
            original_model.song_set,
            original_model.story_set,
            original_model.storypage_set,
        ]

        with transaction.atomic():
            for related_model_set in related_models:
                for related_item in related_model_set.all():
                    # Only convert links to related models that do not have an equivalent audio model
                    if not related_item.related_audio.filter(
                        title=audio_model.title
                    ).exists():
                        related_item.related_audio.add(audio_model)
                        if isinstance(original_model, Image):
                            related_item.related_images.remove(original_model)
                        elif isinstance(original_model, Video):
                            related_item.related_videos.remove(original_model)
                        related_item.save()

    def convert_to_audio_model(self, model):
        with transaction.atomic():
            # convert ImageFile or VideoFile to File
            original_file = model.original

            file = File.objects.create(
                created_by=original_file.created_by,
                created=original_file.created,
                last_modified_by=original_file.last_modified_by,
                last_modified=original_file.last_modified,
                site=original_file.site,
                content=UploadedFile(original_file.content.file),
                mimetype=original_file.mimetype,
                size=original_file.size,
            )

            # create Audio model
            audio_model = Audio.objects.create(
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

            # preserve related model links
            self.convert_model_related_links(model, audio_model)

            # delete original (mismatched) model
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
