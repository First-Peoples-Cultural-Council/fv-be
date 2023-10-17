from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models.media import Audio, Image, Video
from backend.search import ES_RETRY_POLICY
from backend.search.tasks.media_tasks import delete_from_index, update_media_index
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Audio)
@receiver(post_save, sender=Image)
@receiver(post_save, sender=Video)
def request_update_media_index(sender, instance, **kwargs):
    media_model_map = {Audio: "audio", Image: "image", Video: "video"}
    media_type = media_model_map.get(sender, "image")  # defaults to "image"

    # Check if instance exists
    if any(
        model.objects.filter(id=instance.id).exists() for model in [Audio, Image, Video]
    ):
        transaction.on_commit(
            lambda: update_media_index.apply_async(
                (
                    instance.id,
                    media_type,
                ),
                link_error=link_error_handler.s(),
                retry=True,
                retry_policy=ES_RETRY_POLICY,
            )
        )


# Delete entry from index
@receiver(post_delete, sender=Audio)
@receiver(post_delete, sender=Image)
@receiver(post_delete, sender=Video)
def request_delete_from_index(sender, instance, **kwargs):
    delete_from_index.apply_async((instance.id,), link_error=link_error_handler.s())
