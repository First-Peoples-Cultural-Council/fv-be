from django.db.models import signals

from backend.models import (
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
from backend.models.sites import LanguageFamily
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
    sync_site_in_language_index,
    sync_song_in_index,
    sync_song_lyrics_in_index,
    sync_story_in_index,
    sync_story_pages_in_index,
    sync_video_in_index,
)

# Verify the list with signals present in all index documents present in
# backend.search.indexing package if this list goes out of sync
signal_details = {
    "pre_save": [(sync_site_in_language_index, Site), (change_site_visibility, Site)],
    "post_save": [
        (sync_language_family_in_index, LanguageFamily),
        (sync_language_in_index, Language),
        (sync_dictionary_entry_in_index, DictionaryEntry),
        (sync_related_dictionary_entry_in_index, DictionaryEntryCategory),
        (sync_song_in_index, Song),
        (sync_song_lyrics_in_index, Lyric),
        (sync_story_in_index, Story),
        (sync_story_pages_in_index, StoryPage),
        (sync_audio_in_index, Audio),
        (sync_image_in_index, Image),
        (sync_video_in_index, Video),
    ],
    "pre_delete": [
        (remove_language_from_index, Language),
        (remove_site_from_language_index, Site),
        (remove_song_from_index, Song),
    ],
    "post_delete": [
        (remove_dictionary_entry_from_index, DictionaryEntry),
        (sync_related_dictionary_entry_in_index, DictionaryEntryCategory),
        (remove_all_site_content, Site),
        (sync_song_lyrics_in_index, Lyric),
        (remove_story_from_index, Story),
        (sync_story_pages_in_index, StoryPage),
        (remove_audio_from_index, Audio),
        (remove_image_from_index, Image),
        (remove_video_from_index, Video),
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
