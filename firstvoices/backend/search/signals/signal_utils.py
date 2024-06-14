from django.db.models import signals

from backend.models import (
    Category,
    DictionaryEntry,
    Language,
    Lyric,
    Site,
    Song,
    Story,
    StoryPage,
)
from backend.models.dictionary import DictionaryEntryCategory
from backend.models.media import Audio, Image, Video
from backend.models.signals import (
    request_update_mtd_index,
    request_update_mtd_index_category_ops,
    store_current_visibility,
)
from backend.models.sites import LanguageFamily, SiteFeature
from backend.search.signals import (
    change_site_visibility,
    remove_all_site_content,
    remove_audio_from_index,
    remove_dictionary_entry_from_index,
    remove_image_from_index,
    remove_language_from_index,
    remove_site_from_language_index,
    remove_song_from_index,
    remove_story_from_index,
    remove_video_from_index,
    sync_audio_in_index,
    sync_dictionary_entry_in_index,
    sync_image_in_index,
    sync_language_family_in_index,
    sync_language_in_index,
    sync_related_dictionary_entry_in_index,
    sync_site_features_in_media_indexes,
    sync_site_in_language_index,
    sync_song_in_index,
    sync_song_lyrics_in_index,
    sync_story_in_index,
    sync_story_pages_in_index,
    sync_video_in_index,
)

# Verify the list with signals present in all index documents present in
# backend.search.indexing and backend.models.signals packages if this list goes out of sync
signal_details = {
    "pre_save": [
        (sync_site_in_language_index, Site),
        (change_site_visibility, Site),
        (store_current_visibility, DictionaryEntry),
    ],
    "post_save": [
        (request_update_mtd_index_category_ops, Category),
        (sync_language_family_in_index, LanguageFamily),
        (sync_language_in_index, Language),
        (sync_dictionary_entry_in_index, DictionaryEntry),
        (request_update_mtd_index, DictionaryEntry),
        (sync_related_dictionary_entry_in_index, DictionaryEntryCategory),
        (sync_song_in_index, Song),
        (sync_song_lyrics_in_index, Lyric),
        (sync_story_in_index, Story),
        (sync_story_pages_in_index, StoryPage),
        (sync_audio_in_index, Audio),
        (sync_image_in_index, Image),
        (sync_video_in_index, Video),
        (sync_site_features_in_media_indexes, SiteFeature),
    ],
    "pre_delete": [
        (remove_language_from_index, Language),
        (remove_site_from_language_index, Site),
        (remove_song_from_index, Song),
    ],
    "post_delete": [
        (request_update_mtd_index_category_ops, Category),
        (remove_dictionary_entry_from_index, DictionaryEntry),
        (request_update_mtd_index, DictionaryEntry),
        (sync_related_dictionary_entry_in_index, DictionaryEntryCategory),
        (remove_all_site_content, Site),
        (sync_song_lyrics_in_index, Lyric),
        (remove_story_from_index, Story),
        (sync_story_pages_in_index, StoryPage),
        (remove_audio_from_index, Audio),
        (remove_image_from_index, Image),
        (remove_video_from_index, Video),
        (sync_site_features_in_media_indexes, SiteFeature),
    ],
}


def disconnect_signals():
    for signal_name, details in signal_details.items():
        signal = getattr(signals, signal_name)
        for handler, sender in details:
            signal.disconnect(handler, sender=sender)


def connect_signals():
    for signal_name, details in signal_details.items():
        signal = getattr(signals, signal_name)
        for handler, sender in details:
            signal.connect(handler, sender=sender)


INDEXING_PAUSED_FEATURE = "indexing_paused"


def pause_indexing(site):
    feature = SiteFeature.objects.get_or_create(site=site, key=INDEXING_PAUSED_FEATURE)
    feature.is_enabled = True
    feature.save()


def unpause_indexing(site):
    feature = SiteFeature.objects.get_or_create(site=site, key=INDEXING_PAUSED_FEATURE)
    feature.is_enabled = False
    feature.save()


def is_indexing_paused(site):
    if not site.sitefeature_set.filter(key=INDEXING_PAUSED_FEATURE).exists():
        return False
    return site.sitefeature_set.get(key=INDEXING_PAUSED_FEATURE).is_enabled
