from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models.story import Story, StoryPage
from backend.search.indexing.story_index import StoryDocumentManager
from backend.search.signals.site_signals import indexing_signals_paused
from backend.search.tasks.index_manager_tasks import (
    request_remove_from_index,
    request_sync_in_index,
    request_update_in_index,
)


@receiver(post_save, sender=Story)
def sync_story_in_index(sender, instance, **kwargs):
    if not indexing_signals_paused(instance):
        request_sync_in_index(StoryDocumentManager, instance)


@receiver(post_delete, sender=Story)
def remove_story_from_index(sender, instance, **kwargs):
    if not indexing_signals_paused(instance):
        request_remove_from_index(StoryDocumentManager, instance)


@receiver(post_delete, sender=StoryPage)
@receiver(post_save, sender=StoryPage)
def sync_story_pages_in_index(sender, instance, **kwargs):
    if not indexing_signals_paused(instance):
        request_update_in_index(StoryDocumentManager, instance.story)
