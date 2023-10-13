from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models.media import Image
from backend.search import ES_RETRY_POLICY
from backend.search.tasks.media_tasks import delete_from_index, update_media_index
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Image)
def request_update_media_index(sender, instance, **kwargs):
    if Image.objects.filter(id=instance.id).exists():
        update_media_index.apply_async(
            (
                instance.id,
                "image",
            ),
            link_error=link_error_handler.s(),
            retry=True,
            retry_policy=ES_RETRY_POLICY,
        )


# Delete entry from index
@receiver(post_delete, sender=Image)
def request_delete_from_index(sender, instance, **kwargs):
    delete_from_index.apply_async((instance.id,), link_error=link_error_handler.s())
