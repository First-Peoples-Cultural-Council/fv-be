from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models.media import Audio, Document, Image, Video
from backend.search.indexing import (
    AudioDocumentManager,
    DocumentDocumentManager,
    ImageDocumentManager,
    VideoDocumentManager,
)
from backend.search.tasks.index_manager_tasks import (
    request_remove_from_index,
    request_sync_in_index,
)


@receiver(post_save, sender=Audio)
def sync_audio_in_index(sender, instance, **kwargs):
    request_sync_in_index(AudioDocumentManager, instance)


@receiver(post_delete, sender=Audio)
def remove_audio_from_index(sender, instance, **kwargs):
    request_remove_from_index(AudioDocumentManager, instance)


@receiver(post_save, sender=Document)
def sync_document_in_index(sender, instance, **kwargs):
    request_sync_in_index(DocumentDocumentManager, instance)


@receiver(post_delete, sender=Document)
def remove_document_from_index(sender, instance, **kwargs):
    request_remove_from_index(DocumentDocumentManager, instance)


@receiver(post_save, sender=Image)
def sync_image_in_index(sender, instance, **kwargs):
    request_sync_in_index(ImageDocumentManager, instance)


@receiver(post_delete, sender=Image)
def remove_image_from_index(sender, instance, **kwargs):
    request_remove_from_index(ImageDocumentManager, instance)


@receiver(post_save, sender=Video)
def sync_video_in_index(sender, instance, **kwargs):
    request_sync_in_index(VideoDocumentManager, instance)


@receiver(post_delete, sender=Video)
def remove_video_from_index(sender, instance, **kwargs):
    request_remove_from_index(VideoDocumentManager, instance)
