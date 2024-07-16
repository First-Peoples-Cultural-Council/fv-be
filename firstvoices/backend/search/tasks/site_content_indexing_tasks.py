from celery import shared_task
from django.db import transaction

from backend.models import Site
from backend.search.indexing import (
    AudioDocumentManager,
    DictionaryEntryDocumentManager,
    ImageDocumentManager,
    SongDocumentManager,
    StoryDocumentManager,
    VideoDocumentManager,
)
from firstvoices.celery import link_error_handler


# special tasks for bulk Site content indexing actions
def remove_all(document_manager, queryset):
    for instance in queryset:
        document_manager.remove_from_index(instance.id)


@shared_task
def remove_all_site_content_from_indexes(site_id):
    site = Site.objects.get(id=site_id)

    remove_all(DictionaryEntryDocumentManager, site.dictionaryentry_set.all())
    remove_all(SongDocumentManager, site.song_set.all())
    remove_all(StoryDocumentManager, site.story_set.all())
    remove_all(AudioDocumentManager, site.audio_set.all())
    remove_all(ImageDocumentManager, site.image_set.all())
    remove_all(VideoDocumentManager, site.video_set.all())


def sync_all(document_manager, queryset):
    for instance in queryset:
        document_manager.sync_in_index(instance.id)


@shared_task
def sync_all_site_content_in_indexes(site_id):
    site = Site.objects.get(id=site_id)

    sync_all(DictionaryEntryDocumentManager, site.dictionaryentry_set.all())
    sync_all(SongDocumentManager, site.song_set.all())
    sync_all(StoryDocumentManager, site.story_set.all())
    sync_all_media_site_content_in_indexes(site_id)


@shared_task
def sync_all_media_site_content_in_indexes(site_id):
    site = Site.objects.get(id=site_id)

    sync_all(AudioDocumentManager, site.audio_set.all())
    sync_all(ImageDocumentManager, site.image_set.all())
    sync_all(VideoDocumentManager, site.video_set.all())


def request_remove_all_site_content_from_indexes(site):
    transaction.on_commit(
        lambda: remove_all_site_content_from_indexes.apply_async(
            (site.id,),
            link_error=link_error_handler.s(),
        )
    )


def request_sync_all_site_content_in_indexes(site):
    transaction.on_commit(
        lambda: sync_all_site_content_in_indexes.apply_async(
            (site.id,),
            link_error=link_error_handler.s(),
        )
    )


def request_sync_all_media_site_content_in_indexes(site):
    transaction.on_commit(
        lambda: sync_all_media_site_content_in_indexes.apply_async(
            (site.id,),
            link_error=link_error_handler.s(),
        )
    )
