from celery import shared_task

from backend.search.indexing import (
    AudioDocumentManager,
    DictionaryEntryDocumentManager,
    ImageDocumentManager,
    SongDocumentManager,
    StoryDocumentManager,
    VideoDocumentManager,
)

# special tasks for bulk Site content indexing actions


def remove_all(document_manager, queryset):
    for instance in queryset:
        document_manager.remove_from_index(instance.id)


@shared_task
def remove_all_site_content_from_indexes(site):
    remove_all(DictionaryEntryDocumentManager, site.dictionaryentry_set.all())
    remove_all(SongDocumentManager, site.song_set.all())
    remove_all(StoryDocumentManager, site.story_set.all())
    remove_all(AudioDocumentManager, site.audio_set.all())
    remove_all(ImageDocumentManager, site.image_set.all())
    remove_all(VideoDocumentManager, site.video_set.all())
