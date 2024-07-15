from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from backend.models.sites import Site
from backend.search.tasks.site_content_indexing_tasks import (
    remove_all_site_content_from_indexes,
    sync_all_site_content_in_indexes,
)
from firstvoices.celery import link_error_handler


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

    transaction.on_commit(
        lambda: sync_all_site_content_in_indexes.apply_async(
            (instance.id,),
            link_error=link_error_handler.s(),
        )
    )


# If a site is deleted, delete all docs from index related to site
@receiver(post_delete, sender=Site)
def remove_all_site_content(sender, instance, **kwargs):
    site_id = instance.id
    transaction.on_commit(
        lambda: remove_all_site_content_from_indexes.apply_async(
            (site_id,),
            link_error=link_error_handler.s(),
        )
    )


def indexing_signals_paused(site):
    if not site.sitefeature_set.filter(key="indexing_paused").exists():
        return False
    return site.sitefeature_set.get(key="indexing_paused").is_enabled
