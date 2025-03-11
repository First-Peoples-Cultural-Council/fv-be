from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from backend.models.sites import Site
from backend.search.tasks.site_content_indexing_tasks import (
    request_remove_all_site_content_from_indexes,
    request_sync_all_site_content_in_indexes,
)


@receiver(pre_save, sender=Site)
def change_site_visibility(sender, instance, **kwargs):
    """When a Site's visibility changes, update all entry indexes"""
    if not instance.id:
        # new site, no changes needed
        return

    original_site = Site.objects.filter(id=instance.id)

    if (not original_site.exists()) or (
        original_site.first().visibility == instance.visibility
    ):
        # no changes needed
        return

    request_sync_all_site_content_in_indexes(instance)


# If a site is deleted, delete all docs from index related to site
@receiver(post_delete, sender=Site)
def remove_all_site_content(sender, instance, **kwargs):
    site_title = instance.title
    site_content_ids = {
        "dictionaryentry_set": list(
            instance.dictionaryentry_set.values_list("id", flat=True)
        ),
        "song_set": list(instance.song_set.values_list("id", flat=True)),
        "story_set": list(instance.story_set.values_list("id", flat=True)),
        "audio_set": list(instance.audio_set.values_list("id", flat=True)),
        "document_set": list(instance.document_set.values_list("id", flat=True)),
        "image_set": list(instance.image_set.values_list("id", flat=True)),
        "video_set": list(instance.video_set.values_list("id", flat=True)),
    }
    request_remove_all_site_content_from_indexes(site_title, site_content_ids)


def indexing_signals_paused(site):
    if not site.sitefeature_set.filter(key="indexing_paused").exists():
        return False
    return site.sitefeature_set.get(key="indexing_paused").is_enabled
