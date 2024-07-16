from celery import shared_task
from celery.utils.log import get_task_logger

from backend.search.indexing import (
    AudioDocumentManager,
    DictionaryEntryDocumentManager,
    ImageDocumentManager,
    SongDocumentManager,
    StoryDocumentManager,
    VideoDocumentManager,
)
from backend.tasks.utils import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE

# special tasks for bulk Site content indexing actions


def remove_all(document_manager, queryset):
    for instance in queryset:
        document_manager.remove_from_index(instance.id)


@shared_task
def remove_all_site_content_from_indexes(site):
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"site: {site}")

    remove_all(DictionaryEntryDocumentManager, site.dictionaryentry_set.all())
    remove_all(SongDocumentManager, site.song_set.all())
    remove_all(StoryDocumentManager, site.story_set.all())
    remove_all(AudioDocumentManager, site.audio_set.all())
    remove_all(ImageDocumentManager, site.image_set.all())
    remove_all(VideoDocumentManager, site.video_set.all())

    logger.info(ASYNC_TASK_END_TEMPLATE)


def sync_all(document_manager, queryset):
    for instance in queryset:
        document_manager.sync_in_index(instance.id)


@shared_task
def sync_all_site_content_in_indexes(site):
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"site: {site}")

    sync_all(DictionaryEntryDocumentManager, site.dictionaryentry_set.all())
    sync_all(SongDocumentManager, site.song_set.all())
    sync_all(StoryDocumentManager, site.story_set.all())
    sync_all_media_site_content_in_indexes(site)

    logger.info(ASYNC_TASK_END_TEMPLATE)


@shared_task
def sync_all_media_site_content_in_indexes(site):
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"site: {site}")

    sync_all(AudioDocumentManager, site.audio_set.all())
    sync_all(ImageDocumentManager, site.image_set.all())
    sync_all(VideoDocumentManager, site.video_set.all())

    logger.info(ASYNC_TASK_END_TEMPLATE)
