from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from backend.models.sites import Site
from backend.search.indexing import (
    DictionaryIndexManager,
    MediaIndexManager,
    SongIndexManager,
    StoryIndexManager,
)
from backend.search.tasks.index_manager_tasks import request_rebuild_for_site
from backend.search.tasks.site_content_indexing_tasks import (
    remove_all_site_content_from_indexes,
)


@receiver(pre_save, sender=Site)
def change_site_visibility(sender, instance, **kwargs):
    """When a Site's visibility changes, update all entry indexes"""
    request_rebuild_for_site(SongIndexManager, instance)
    request_rebuild_for_site(StoryIndexManager, instance)
    request_rebuild_for_site(DictionaryIndexManager, instance)
    request_rebuild_for_site(MediaIndexManager, instance)


# If a site is deleted, delete all docs from index related to site
@receiver(post_delete, sender=Site)
def request_delete_related_docs(sender, instance, **kwargs):
    remove_all_site_content_from_indexes(instance)
