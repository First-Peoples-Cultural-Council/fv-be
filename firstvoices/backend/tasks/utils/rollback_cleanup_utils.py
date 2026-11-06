from celery.utils.log import get_task_logger
from django.db import transaction

from backend.models.jobs import JobStatus
from backend.models.media import Audio, AudioSpeaker, Document, Image, Video
from backend.models.update_jobs import RollbackJob, UpdateJobStatus

MEDIA_MODELS = (Audio, Document, Image, Video)


def has_content_references(instance):
    """
    Check whether any other content is currently using this media or file,
    e.g. songs, stories, other dictionary entries outside of the current update job, etc.
    """
    for relation in instance._meta.related_objects:
        # Skip AudioSpeaker relations as they are deleted along with the audio instance.
        if relation.related_model is AudioSpeaker:
            continue

        related_model = relation.related_model
        reference_filter = {relation.field.name: instance.id}

        if related_model.objects.filter(**reference_filter).exists():
            return True

    return False


def delete_orphaned_media_records(update_job):
    """
    Delete unused media and file database records, then return their file objects.
    """
    files_to_check = []
    files_to_delete = []

    # Keep database cleanup separate from storage deletion, S3 cannot be rolled back.
    with transaction.atomic():
        # Remove unused job-created media, keeping their files for a separate check.
        for media_model in MEDIA_MODELS:
            job_media = media_model.objects.filter(
                site=update_job.site,
                original__site=update_job.site,
                original__update_job=update_job,
            )
            for media in job_media:
                if has_content_references(media):
                    continue

                files_to_check.append(media.original)

                # Image and video previews have their own file records.
                if isinstance(media, (Image, Video)):
                    for size_name in ("thumbnail", "small", "medium"):
                        thumbnail_file = getattr(media, size_name)
                        if thumbnail_file is not None:
                            files_to_check.append(thumbnail_file)

                # Instance deletion also deletes originals and thumbnails. Check
                # those separately below so a shared file is not deleted.
                media_model.objects.filter(id=media.id).delete()

        # Delete file records only after checking for references from remaining content.
        for file in files_to_check:
            file_model = type(file)
            if not file_model.objects.filter(id=file.id).exists():
                continue
            if has_content_references(file):
                continue
            files_to_delete.append(file)
            file_model.objects.filter(id=file.id).delete()

    # These objects have been deleted from the DB, but they hold the storage paths for deletion.
    return files_to_delete


def cleanup_rollback_media(rollback_job_id):
    logger = get_task_logger(__name__)

    try:
        # Never clean up media before the entry restoration has succeeded.
        rollback_job = RollbackJob.objects.select_related("update_job").get(
            id=rollback_job_id
        )
        if (
            rollback_job.status != JobStatus.COMPLETE
            or rollback_job.update_job.status != UpdateJobStatus.ROLLED_BACK
        ):
            logger.warning(
                "Rollback %s has not completed; skipping cleanup.", rollback_job_id
            )
            return
        # Commit database cleanup before making any irreversible storage calls.
        files_to_delete = delete_orphaned_media_records(rollback_job.update_job)
    except Exception:
        logger.exception(
            "Failed to delete orphaned records for rollback %s.", rollback_job_id
        )
        return

    # Storage cleanup is best-effort and does not change the completed rollback status.
    for file in files_to_delete:
        try:
            file.content.delete(save=False)
        except Exception:
            # Failed files may need manual cleanup; continue with the remaining files.
            logger.exception(
                "Failed to delete %s %s from storage (%s) for rollback %s.",
                file._meta.model_name,
                file.id,
                file.content.name,
                rollback_job_id,
            )
