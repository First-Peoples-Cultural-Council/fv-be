from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models.story import Story, StoryPage
from backend.search.tasks import story_index_tasks
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Story)
def sync_story_in_index(sender, instance, **kwargs):
    story_index_tasks.sync_story_in_index.apply_async(
        (instance.id,), link_error=link_error_handler.s()
    )


@receiver(post_delete, sender=Story)
def remove_story_from_index(sender, instance, **kwargs):
    story_index_tasks.remove_story_from_index.apply_async(
        (instance.id,), link_error=link_error_handler.s()
    )


@receiver(post_delete, sender=StoryPage)
@receiver(post_save, sender=StoryPage)
def sync_story_pages_in_index(sender, instance, **kwargs):
    story_index_tasks.sync_story_in_index.apply_async(
        (instance.story.id,), link_error=link_error_handler.s()
    )
