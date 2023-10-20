from django.core.management import BaseCommand

from backend.tasks.update_metadata_tasks import (
    update_missing_audio_metadata,
    update_missing_image_metadata,
    update_missing_video_metadata,
)


class Command(BaseCommand):
    def handle(self, **options):
        """
        This command is used to update the metadata for all media files that are missing metadata.
        It will queue up each of the three update tasks (image/video/audio) in a separate Celery worker.
        """

        update_missing_image_metadata.apply_async()
        update_missing_video_metadata.apply_async()
        update_missing_audio_metadata.apply_async()
