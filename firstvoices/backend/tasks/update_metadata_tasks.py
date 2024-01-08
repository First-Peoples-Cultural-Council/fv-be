import logging

from celery import shared_task
from django.db.models import Q

from backend.models.media import File, ImageFile, VideoFile


def update_missing_media_metadata(missing_media_files):
    logger = logging.getLogger(__name__)

    # Update the metadata for each file object using the save method on the model
    logger.debug(
        f"Updating metadata for {missing_media_files.count()} {missing_media_files.first().__class__.__name__} file(s)."
    )
    for file in missing_media_files:
        try:
            file.save(update_file_metadata=True)
        except FileNotFoundError as e:
            logger.warning(
                f"File not found for {file.__class__.__name__} - {file.id}. Error: {e}"
            )
        except Exception as e:
            logger.warning(
                f"File could not be updated for {file.__class__.__name__} - {file.id}. Error: {e}"
            )
        else:
            logger.debug(
                f"Successfully updated metadata for {file.__class__.__name__} - {file.id} with path {file.content}."
            )


@shared_task
def update_missing_image_metadata():
    """
    Updates the metadata for all ImageFile objects that are missing mimetype, size, height, or width metadata.
    Also updates when the height or width is set to the migration import default of -1.
    """

    # Gather the ImageFile objects that are missing metadata
    missing_metadata_images = ImageFile.objects.filter(
        Q(height=-1)
        | Q(height=None)
        | Q(width=-1)
        | Q(width=None)
        | Q(size=None)
        | Q(mimetype=None)
        | Q(mimetype="")
    ).all()

    # Update the metadata for each ImageFile object using the save method on the model
    update_missing_media_metadata(missing_metadata_images)


@shared_task
def update_missing_video_metadata():
    """
    Updates the metadata for all VideoFile objects that are missing mimetype, size, height, or width metadata.
    Also updates when the height or width is set to the migration import default of -1.
    """

    # Gather the VideoFile objects that are missing metadata
    missing_metadata_videos = VideoFile.objects.filter(
        Q(height=-1)
        | Q(height=None)
        | Q(width=-1)
        | Q(width=None)
        | Q(size=None)
        | Q(mimetype=None)
        | Q(mimetype="")
    ).all()

    # Update the metadata for each VideoFile object using the save method on the model
    update_missing_media_metadata(missing_metadata_videos)


@shared_task
def update_missing_audio_metadata():
    """
    Updates the metadata for all File (audio) objects that are missing mimetype, or size metadata.
    """

    # Gather the File (audio) objects that are missing metadata
    missing_metadata_audio = File.objects.filter(
        Q(size=None) | Q(mimetype=None) | Q(mimetype="")
    ).all()

    # Update the metadata for each File (audio) object using the save method on the model
    update_missing_media_metadata(missing_metadata_audio)
