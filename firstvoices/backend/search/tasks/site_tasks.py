import logging

from celery import shared_task
from elasticsearch.exceptions import ConnectionError, NotFoundError

from backend.models.sites import Site
from backend.search.documents import (
    DictionaryEntryDocument,
    MediaDocument,
    SongDocument,
    StoryDocument,
)
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_MEDIA_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    RETRY_ON_CONFLICT,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_object_from_index
from firstvoices.settings import ELASTICSEARCH_LOGGER


@shared_task
def update_document_visibility(instance_id, instance_visibility, **kwargs):
    instance = Site.objects.get(id=instance_id)
    dictionary_entries_set = instance.dictionaryentry_set.all()
    songs_set = instance.song_set.all()
    stories_set = instance.story_set.all()
    audio_set = instance.audio_set.all()
    image_set = instance.image_set.all()
    video_set = instance.video_set.all()

    # Updating dictionary_entries visibility
    for dictionary_entry in dictionary_entries_set:
        update_dictionary_entry_visibility(dictionary_entry, instance_visibility)

    # Updating songs visibility
    for song in songs_set:
        update_song_visibility(song, instance_visibility)

    # updating story visibility
    for story in stories_set:
        update_story_visibility(story, instance_visibility)

    # Updating media visibility
    for audio in audio_set:
        update_media_visibility(audio, instance_visibility)
    for image in image_set:
        update_media_visibility(image, instance_visibility)
    for video in video_set:
        update_media_visibility(video, instance_visibility)


@shared_task
def delete_related_docs(instance_id, **kwargs):
    instance = Site.objects.get(id=instance_id)
    dictionary_entries_set = instance.dictionaryentry_set.all()
    songs_set = instance.song_set.all()
    stories_set = instance.story_set.all()
    audio_set = instance.audio_set.all()
    image_set = instance.image_set.all()
    video_set = instance.video_set.all()

    # removing dictionary_entries related to the deleted site
    for dictionary_entry in dictionary_entries_set:
        remove_dictionary_entry_from_index(dictionary_entry)

    # removing songs related to the deleted site
    for song in songs_set:
        remove_song_from_index(song)

    # removing story related to the deleted site
    for story in stories_set:
        remove_story_from_index(story)

    # removing media related to deleted site
    for audio in audio_set:
        remove_media_from_index(audio)
    for image in image_set:
        remove_media_from_index(image)
    for video in video_set:
        remove_media_from_index(video)


# The following update and delete methods can be optimized using bulk operation
def update_dictionary_entry_visibility(dictionary_entry, updated_visibility):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "dictionary_entry",
            dictionary_entry.id,
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(
            site_visibility=updated_visibility, retry_on_conflict=RETRY_ON_CONFLICT
        )
    except ConnectionError:
        logger.warning(
            ES_CONNECTION_ERROR
            % (
                "dictionary_entry",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry.id,
            )
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "sites_visibility_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            type(e).__name__,
            SearchIndexEntryTypes.DICTIONARY_ENTRY,
            dictionary_entry.id,
        )
        logger.error(e)


def update_song_visibility(song, updated_visibility):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_SONG_INDEX, "song", song.id
        )
        if not existing_entry:
            raise NotFoundError

        song_doc = SongDocument.get(id=existing_entry["_id"])
        song_doc.update(
            site_visibility=updated_visibility, retry_on_conflict=RETRY_ON_CONFLICT
        )
    except ConnectionError:
        logger.warning(
            ES_CONNECTION_ERROR % ("song", SearchIndexEntryTypes.SONG, song.id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "sites_visibility_update_signal",
                SearchIndexEntryTypes.SONG,
                song.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.SONG, song.id)
        logger.error(e)


def update_story_visibility(story, updated_visibility):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_STORY_INDEX, "story", story.id
        )
        if not existing_entry:
            raise NotFoundError

        story_doc = StoryDocument.get(id=existing_entry["_id"])
        story_doc.update(
            site_visibility=updated_visibility, retry_on_conflict=RETRY_ON_CONFLICT
        )
    except ConnectionError:
        logger.warning(
            ES_CONNECTION_ERROR % ("story", SearchIndexEntryTypes.STORY, story.id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "sites_visibility_update_signal",
                SearchIndexEntryTypes.STORY,
                story.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, story.id)
        logger.error(e)


def update_media_visibility(media_instance, updated_visibility):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_MEDIA_INDEX, "media", media_instance.id
        )
        if not existing_entry:
            raise NotFoundError

        media_doc = MediaDocument.get(id=existing_entry["_id"])
        media_doc.update(
            site_visibility=updated_visibility, retry_on_conflict=RETRY_ON_CONFLICT
        )
    except ConnectionError:
        logger.warning(
            ES_CONNECTION_ERROR
            % ("media", SearchIndexEntryTypes.MEDIA, media_instance.id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "sites_visibility_update_signal",
                SearchIndexEntryTypes.MEDIA,
                media_instance.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.MEDIA, media_instance.id)
        logger.error(e)


def remove_dictionary_entry_from_index(dictionary_entry):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "dictionary_entry",
            dictionary_entry.id,
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % (
                "dictionary_entry",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry.id,
            )
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "sites_delete_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            type(e).__name__,
            SearchIndexEntryTypes.DICTIONARY_ENTRY,
            dictionary_entry.id,
        )
        logger.error(e)


def remove_song_from_index(song):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_SONG_INDEX, "song", song.id
        )
        if not existing_entry:
            raise NotFoundError

        song_doc = SongDocument.get(id=existing_entry["_id"])
        song_doc.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR % ("song", SearchIndexEntryTypes.SONG, song.id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "sites_delete_signal",
                SearchIndexEntryTypes.SONG,
                song.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.SONG, song.id)
        logger.error(e)


def remove_story_from_index(story):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_STORY_INDEX, "story", story.id
        )
        if not existing_entry:
            raise NotFoundError

        story_doc = StoryDocument.get(id=existing_entry["_id"])
        story_doc.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR % ("story", SearchIndexEntryTypes.STORY, story.id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "sites_delete_signal",
                SearchIndexEntryTypes.STORY,
                story.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, story.id)
        logger.error(e)


def remove_media_from_index(media_instance):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_MEDIA_INDEX, "media", media_instance.id
        )
        if not existing_entry:
            raise NotFoundError

        media_doc = MediaDocument.get(id=existing_entry["_id"])
        media_doc.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("media", SearchIndexEntryTypes.MEDIA, media_instance.id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "sites_delete_signal",
                SearchIndexEntryTypes.MEDIA,
                media_instance.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.MEDIA, media_instance.id)
        logger.error(e)
