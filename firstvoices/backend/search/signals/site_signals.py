from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from backend.models.sites import Site, SiteFeature
from backend.search.tasks.site_content_indexing_tasks import (
    remove_all_site_content_from_indexes,
    sync_all_media_site_content_in_indexes,
    sync_all_site_content_in_indexes,
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

    sync_all_site_content_in_indexes(instance)


# If a site is deleted, delete all docs from index related to site
@receiver(post_delete, sender=Site)
def remove_all_site_content(sender, instance, **kwargs):
    remove_all_site_content_from_indexes(instance)


@receiver(post_save, sender=SiteFeature)
@receiver(post_delete, sender=SiteFeature)
def sync_site_features_in_media_indexes(sender, instance, **kwargs):
    site = instance.site
    sync_all_media_site_content_in_indexes(site)
