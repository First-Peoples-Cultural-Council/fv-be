import logging

from celery import shared_task
from django.db.models import Q

from backend.models.media import File, ImageFile, VideoFile


@shared_task
def update_missing_image_metadata():
    """
    Updates the metadata for all ImageFile objects that are missing mimetype, size, height, or width metadata.
    Also updates when the height or width is set to the migration import default of -1.
    """

    logger = logging.getLogger(__name__)

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
    logger.info(
        f"Updating metadata for {missing_metadata_images.count()} image file(s)."
    )
    for image in missing_metadata_images:
        try:
            image.save(update_metadata_command=True)
        except FileNotFoundError as e:
            logger.warning(f"File not found for ImageFile {image.id}. Error: {e}")
        else:
            logger.info(
                f"Successfully updated metadata for ImageFile {image.id} with path {image.content}."
            )


@shared_task
def update_missing_video_metadata():
    """
    Updates the metadata for all VideoFile objects that are missing mimetype, size, height, or width metadata.
    Also updates when the height or width is set to the migration import default of -1.
    """

    logger = logging.getLogger(__name__)

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
    logger.info(
        f"Updating metadata for {missing_metadata_videos.count()} video file(s)."
    )
    for video in missing_metadata_videos:
        try:
            video.save(update_metadata_command=True)
        except FileNotFoundError as e:
            logger.warning(f"File not found for VideoFile {video.id}. Error: {e}")
        else:
            logger.info(
                f"Successfully updated metadata for VideoFile {video.id} with path {video.content}."
            )


@shared_task
def update_missing_audio_metadata():
    """
    Updates the metadata for all File (audio) objects that are missing mimetype, or size metadata.
    """

    logger = logging.getLogger(__name__)

    # Gather the File (audio) objects that are missing metadata
    missing_metadata_audio = File.objects.filter(
        Q(size=None) | Q(mimetype=None) | Q(mimetype="")
    ).all()

    # Update the metadata for each File (audio) object using the save method on the model
    logger.info(
        f"Updating metadata for {missing_metadata_audio.count()} audio file(s)."
    )
    for audio in missing_metadata_audio:
        try:
            audio.save(update_metadata_command=True)
        except FileNotFoundError as e:
            logger.warning(f"File not found for audio File {audio.id}. Error: {e}")
        else:
            logger.info(
                f"Successfully updated metadata for audio File {audio.id} with path {audio.content}."
            )
