from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models.story import Story, StoryPage
from backend.search import ES_RETRY_POLICY
from backend.search.tasks.story_tasks import (
    delete_from_index,
    delete_pages,
    update_pages,
    update_story_index,
)
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Story)
def request_update_story_index(sender, instance, **kwargs):
    if Story.objects.filter(id=instance.id).exists():
        if instance.title == "":
            return
        else:
            update_story_index.apply_async(
                (instance.id,),
                link_error=link_error_handler.s(),
                retry=True,
                retry_policy=ES_RETRY_POLICY,
            )


# Delete entry from index
@receiver(post_delete, sender=Story)
def request_delete_from_index(sender, instance, **kwargs):
    delete_from_index.apply_async((instance.id,), link_error=link_error_handler.s())


# Page update
@receiver(post_save, sender=StoryPage)
def request_update_pages_index(sender, instance, **kwargs):
    if Story.objects.filter(id=instance.story_id).exists():
        update_pages.apply_async(
            (
                instance.id,
                instance.story_id,
            ),
            countdown=10,
            link_error=link_error_handler.s(),
            retry=True,
            retry_policy=ES_RETRY_POLICY,
        )


@receiver(post_delete, sender=StoryPage)
def request_delete_story_page_from_index(sender, instance, **kwargs):
    delete_pages.apply_async((instance.story_id,), link_error=link_error_handler.s())
