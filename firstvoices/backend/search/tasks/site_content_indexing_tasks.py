from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction

from backend.models import Site
from backend.search.indexing import (
    AudioDocumentManager,
    DictionaryEntryDocumentManager,
    DocumentDocumentManager,
    ImageDocumentManager,
    SongDocumentManager,
    StoryDocumentManager,
    VideoDocumentManager,
)
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE
from firstvoices.celery import link_error_handler


# special tasks for bulk Site content indexing actions
def remove_all(document_manager, queryset):
    for instance_id in queryset:
        document_manager.remove_from_index(instance_id)


@shared_task
def remove_all_site_content_from_indexes(site_title, site_content_ids):
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"site: {site_title}")

    remove_all(DictionaryEntryDocumentManager, site_content_ids["dictionaryentry_set"])
    remove_all(SongDocumentManager, site_content_ids["song_set"])
    remove_all(StoryDocumentManager, site_content_ids["story_set"])
    remove_all(AudioDocumentManager, site_content_ids["audio_set"])
    remove_all(DocumentDocumentManager, site_content_ids["document_set"])
    remove_all(ImageDocumentManager, site_content_ids["image_set"])
    remove_all(VideoDocumentManager, site_content_ids["video_set"])

    logger.info(ASYNC_TASK_END_TEMPLATE)


def sync_all(document_manager, queryset):
    for instance in queryset:
        document_manager.sync_in_index(instance.id)


@shared_task
def sync_all_site_content_in_indexes(site_id):
    site = Site.objects.get(id=site_id)
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"site: {site}")

    sync_all(DictionaryEntryDocumentManager, site.dictionaryentry_set.all())
    sync_all(SongDocumentManager, site.song_set.all())
    sync_all(StoryDocumentManager, site.story_set.all())
    sync_all_media_site_content_in_indexes(site_id)

    logger.info(ASYNC_TASK_END_TEMPLATE)


@shared_task
def sync_all_media_site_content_in_indexes(site_id):
    site = Site.objects.get(id=site_id)
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"site: {site}")

    sync_all(AudioDocumentManager, site.audio_set.all())
    sync_all(DocumentDocumentManager, site.document_set.all())
    sync_all(ImageDocumentManager, site.image_set.all())
    sync_all(VideoDocumentManager, site.video_set.all())

    logger.info(ASYNC_TASK_END_TEMPLATE)


def request_remove_all_site_content_from_indexes(site_title, site_content_ids):
    transaction.on_commit(
        lambda: remove_all_site_content_from_indexes.apply_async(
            (site_title, site_content_ids),
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
