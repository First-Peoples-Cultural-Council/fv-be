from django.core.management import CommandError
from django.db.models import signals
from django.utils import timezone
from elasticsearch.helpers import bulk, errors
from elasticsearch_dsl import Index
from elasticsearch_dsl.connections import connections

from backend.management.commands.utils.iterators import (
    audio_iterator,
    dictionary_entry_iterator,
    image_iterator,
    song_iterator,
    story_iterator,
    video_iterator,
)
from backend.models import (
    Acknowledgement,
    DictionaryEntry,
    Lyric,
    Note,
    Site,
    Song,
    Story,
    StoryPage,
    Translation,
)
from backend.models.dictionary import DictionaryEntryCategory
from backend.models.media import Audio, Image, Video
from backend.search.signals.dictionary_entry_signals import (
    request_delete_dictionary_entry_index,
    request_update_acknowledgement_index,
    request_update_categories_index,
    request_update_categories_m2m_index,
    request_update_dictionary_entry_index,
    request_update_notes_index,
    request_update_translation_index,
)
from backend.search.signals.media_signals import (
    request_delete_from_index as request_delete_from_index_media,
)
from backend.search.signals.media_signals import request_update_media_index
from backend.search.signals.site_signals import (
    request_delete_related_docs,
    request_update_document_visibility,
)
from backend.search.signals.song_signals import (
    request_delete_from_index as request_delete_from_index_song,
)
from backend.search.signals.song_signals import (
    request_update_lyrics_index,
    request_update_song_index,
)
from backend.search.signals.story_signals import (
    request_delete_from_index as request_delete_from_index_story,
)
from backend.search.signals.story_signals import (
    request_delete_story_page_from_index,
    request_update_pages_index,
    request_update_story_index,
)
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_MEDIA_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
)
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG


def rebuild_index(index_name, index_document):
    es = connections.get_connection()

    # Get the latest index
    current_index = get_current_index(es, index_name)

    # Create new index with current timestamp
    current_timestamp = timezone.now().strftime("%Y_%m_%d_%H_%M_%S")
    new_index_name = index_name + "_" + current_timestamp
    new_index = Index(new_index_name)
    new_index.settings(
        number_of_shards=ELASTICSEARCH_DEFAULT_CONFIG["shards"],
        number_of_replicas=ELASTICSEARCH_DEFAULT_CONFIG["replicas"],
    )

    # Appointing the new index as the 'write' index while rebuilding
    new_index.document(index_document)
    new_index = add_write_alias(new_index, index_name)
    new_index.create()

    # Add all documents to the new index
    try:
        if index_name == ELASTICSEARCH_SONG_INDEX:
            bulk(es, song_iterator())
        elif index_name == ELASTICSEARCH_STORY_INDEX:
            bulk(es, story_iterator())
        elif index_name == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            bulk(es, dictionary_entry_iterator())
        elif index_name == ELASTICSEARCH_MEDIA_INDEX:
            bulk(es, image_iterator())
            bulk(es, audio_iterator())
            bulk(es, video_iterator())
    except errors.BulkIndexError as e:
        # Alias configuration error
        if "multiple indices" in str(e):
            raise CommandError(
                "There are multiple indices with same alias. Try clearing all indices and then "
                "rebuilding."
            )
    except Exception as e:
        # Any other exception due to which we are not able to build a new index or add documents to it
        # delete the new index so the current index is default index for both read and write
        new_index.delete(ignore=404)
        raise CommandError(
            "The following error occurred while indexing documents. Deleting new index, "
            + "making current index default. "
            + str(e)
        )

    # Removing old index
    if current_index:
        current_index.delete(ignore=404)

    # Removing and adding alias back to new index
    # This is done to remove the write rule added to this index
    # Only one index can be appointed as write index, for future rebuilding this rule needs to be removed
    # if we have only one index, it's write index by default
    new_index.delete_alias(using=es, name=index_name, ignore=404)
    new_index.put_alias(using=es, name=index_name)


def get_current_index(es_connection, index_name):
    all_indices = es_connection.indices.get_alias(index="*")
    related_indices = []
    for index in all_indices.keys():
        if str(index_name) in str(index):
            related_indices.append(index)

    if len(related_indices):
        related_indices = sorted(related_indices, reverse=True)
        return Index(related_indices[0])
    else:
        return None


def add_write_alias(index, index_name):
    alias_config = {"is_write_index": True}

    if index_name == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
        index.aliases(dictionary_entries=alias_config)
    elif index_name == ELASTICSEARCH_SONG_INDEX:
        index.aliases(songs=alias_config)
    elif index_name == ELASTICSEARCH_STORY_INDEX:
        index.aliases(stories=alias_config)
    elif index_name == ELASTICSEARCH_MEDIA_INDEX:
        index.aliases(media=alias_config)
    return index


def get_valid_index_name(mappings, index_name):
    if index_name in mappings:
        return index_name
    else:
        return None


def disconnect_signals():
    # Disconnect signals temporarily
    # Verify the list with signals present in all index documents present in
    # backend.search folder if this list goes out of sync

    # backend.search.signals.dictionary_entry_signals
    signals.post_save.disconnect(
        request_update_dictionary_entry_index, sender=DictionaryEntry
    )
    signals.post_delete.disconnect(
        request_delete_dictionary_entry_index, sender=DictionaryEntry
    )
    signals.post_save.disconnect(request_update_translation_index, sender=Translation)
    signals.post_delete.disconnect(request_update_translation_index, sender=Translation)
    signals.post_save.disconnect(request_update_notes_index, sender=Note)
    signals.post_delete.disconnect(request_update_notes_index, sender=Note)
    signals.post_save.disconnect(
        request_update_acknowledgement_index, sender=Acknowledgement
    )
    signals.post_delete.disconnect(
        request_update_acknowledgement_index, sender=Acknowledgement
    )
    signals.post_save.disconnect(
        request_update_categories_index, sender=DictionaryEntryCategory
    )
    signals.post_delete.disconnect(
        request_update_categories_index, sender=DictionaryEntryCategory
    )
    signals.m2m_changed.disconnect(
        request_update_categories_m2m_index, sender=DictionaryEntryCategory
    )

    # backend.search.signals.song_signals
    signals.post_save.disconnect(request_update_song_index, sender=Song)
    signals.post_delete.disconnect(request_delete_from_index_song, sender=Song)
    signals.post_save.disconnect(request_update_lyrics_index, sender=Lyric)
    signals.post_delete.disconnect(request_update_lyrics_index, sender=Lyric)

    # backend.search.signals.story_signals
    signals.post_save.disconnect(request_update_story_index, sender=Story)
    signals.post_delete.disconnect(request_delete_from_index_story, sender=Story)
    signals.post_save.disconnect(request_update_pages_index, sender=StoryPage)
    signals.post_delete.disconnect(
        request_delete_story_page_from_index, sender=StoryPage
    )

    # backend.search.signals.media_signals
    signals.post_save.disconnect(request_update_media_index, sender=Audio)
    signals.post_save.disconnect(request_update_media_index, sender=Image)
    signals.post_save.disconnect(request_update_media_index, sender=Video)
    signals.post_delete.disconnect(request_delete_from_index_media, sender=Audio)
    signals.post_delete.disconnect(request_delete_from_index_media, sender=Image)
    signals.post_delete.disconnect(request_delete_from_index_media, sender=Video)

    # backend.search.utils.site_signals
    signals.pre_save.disconnect(request_update_document_visibility, sender=Site)
    signals.post_delete.disconnect(request_delete_related_docs, sender=Site)


def reconnect_signals():
    # Reconnect signals back to models
    # Verify the list with signals present in all index documents present in
    # backend.search folder if this list goes out of sync

    # backend.search.signals.dictionary_entry_signals
    signals.post_save.connect(
        request_update_dictionary_entry_index, sender=DictionaryEntry
    )
    signals.post_delete.connect(
        request_delete_dictionary_entry_index, sender=DictionaryEntry
    )
    signals.post_save.connect(request_update_translation_index, sender=Translation)
    signals.post_delete.connect(request_update_translation_index, sender=Translation)
    signals.post_save.connect(request_update_notes_index, sender=Note)
    signals.post_delete.connect(request_update_notes_index, sender=Note)
    signals.post_save.connect(
        request_update_acknowledgement_index, sender=Acknowledgement
    )
    signals.post_delete.connect(
        request_update_acknowledgement_index, sender=Acknowledgement
    )
    signals.post_save.connect(
        request_update_categories_index, sender=DictionaryEntryCategory
    )
    signals.post_delete.connect(
        request_update_categories_index, sender=DictionaryEntryCategory
    )
    signals.m2m_changed.connect(
        request_update_categories_m2m_index, sender=DictionaryEntryCategory
    )

    # backend.search.signals.song_signals
    signals.post_save.connect(request_update_song_index, sender=Song)
    signals.post_delete.connect(request_delete_from_index_song, sender=Song)
    signals.post_save.connect(request_update_lyrics_index, sender=Lyric)
    signals.post_delete.connect(request_update_lyrics_index, sender=Lyric)

    # backend.search.signals.story_signals
    signals.post_save.connect(request_update_story_index, sender=Story)
    signals.post_delete.connect(request_delete_from_index_story, sender=Story)
    signals.post_save.connect(request_update_pages_index, sender=StoryPage)
    signals.post_delete.connect(request_delete_story_page_from_index, sender=StoryPage)

    # backend.search.signals.media_signals
    signals.post_save.connect(request_update_media_index, sender=Audio)
    signals.post_save.connect(request_update_media_index, sender=Image)
    signals.post_save.connect(request_update_media_index, sender=Video)
    signals.post_delete.connect(request_delete_from_index_media, sender=Audio)
    signals.post_delete.connect(request_delete_from_index_media, sender=Image)
    signals.post_delete.connect(request_delete_from_index_media, sender=Video)

    # backend.search.utils.site_signals
    signals.pre_save.connect(request_update_document_visibility, sender=Site)
    signals.post_delete.connect(request_delete_related_docs, sender=Site)
