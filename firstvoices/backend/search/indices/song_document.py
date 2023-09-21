import logging

from celery import shared_task
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Index, Keyword, Text

from backend.models import Lyric, Song
from backend.search.indices.base_document import BaseDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_SONG_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_lyrics, get_object_from_index
from firstvoices.celery import link_error_handler
from firstvoices.settings import ELASTICSEARCH_LOGGER


class SongDocument(BaseDocument):
    # text search fields
    title = Text(fields={"raw": Keyword()}, copy_to="primary_language_search_fields")
    title_translation = Text(copy_to="primary_translation_search_fields")
    intro_title = Text(copy_to="secondary_language_search_fields")
    intro_translation = Text(copy_to="secondary_translation_search_fields")
    lyrics_text = Text(copy_to="secondary_language_search_fields")
    lyrics_translation = Text(copy_to="secondary_translation_search_fields")
    note = Text(copy_to="other_translation_search_fields")
    acknowledgement = Text(copy_to="other_translation_search_fields")

    class Index:
        name = ELASTICSEARCH_SONG_INDEX


@receiver(post_save, sender=Song)
def request_update_song_index(sender, instance, **kwargs):
    if Song.objects.filter(id=instance.id).exists():
        update_song_index.apply_async(
            (instance.id,), countdown=10, link_error=link_error_handler.s()
        )


@shared_task
def update_song_index(instance_id, **kwargs):
    # add song to es index
    try:
        instance = Song.objects.get(id=instance_id)
        existing_entry = get_object_from_index(
            ELASTICSEARCH_SONG_INDEX, "song", instance.id
        )
        lyrics_text, lyrics_translation_text = get_lyrics(instance)

        if existing_entry:
            # Check if object is already indexed, then update
            index_entry = SongDocument.get(id=existing_entry["_id"])
            index_entry.update(
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=instance.visibility,
                title=instance.title,
                title_translation=instance.title_translation,
                note=instance.notes,
                acknowledgement=instance.acknowledgements,
                intro_title=instance.introduction,
                intro_translation=instance.introduction_translation,
                lyrics_text=lyrics_text,
                lyrics_translation=lyrics_translation_text,
            )
        else:
            index_entry = SongDocument(
                document_id=str(instance.id),
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=instance.visibility,
                title=instance.title,
                title_translation=instance.title_translation,
                note=instance.notes,
                acknowledgement=instance.acknowledgements,
                intro_title=instance.introduction,
                intro_translation=instance.introduction_translation,
                lyrics_text=lyrics_text,
                lyrics_translation=lyrics_translation_text,
            )
            index_entry.save()
        # Refresh the index to ensure the index is up-to-date for related field signals
        song_index = Index(ELASTICSEARCH_SONG_INDEX)
        song_index.refresh()
    except ConnectionError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            ES_CONNECTION_ERROR % ("song", SearchIndexEntryTypes.SONG, instance_id)
        )
        logger.error(e)
    except NotFoundError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.SONG,
            instance_id,
        )
        logger.warning(e)
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.SONG, instance_id)
        logger.error(e)


# Delete entry from index
@receiver(post_delete, sender=Song)
def request_delete_from_index(sender, instance, **kwargs):
    delete_from_index.apply_async((instance.id,), link_error=link_error_handler.s())


@shared_task
def delete_from_index(instance_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_SONG_INDEX, "song", instance_id
        )
        if existing_entry:
            index_entry = SongDocument.get(id=existing_entry["_id"])
            index_entry.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR % ("song", SearchIndexEntryTypes.SONG, instance_id)
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.SONG, instance_id)
        logger.error(e)


# Lyrics update
@receiver(post_delete, sender=Lyric)
@receiver(post_save, sender=Lyric)
def request_update_lyrics(sender, instance, **kwargs):
    update_lyrics.apply_async(
        (instance.id, instance.song.id), countdown=10, link_error=link_error_handler.s()
    )


@shared_task
def update_lyrics(instance_id, song_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    # Set song and lyric text. If it doesn't exist due to deletion, warn and return.
    try:
        song = Song.objects.get(id=song_id)
        lyrics_text, lyrics_translation_text = get_lyrics(song)
    except Song.DoesNotExist:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "lyrics_update_signal",
                SearchIndexEntryTypes.SONG,
                song_id,
            )
        )
        return

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_SONG_INDEX, "song", song.id
        )
        if not existing_entry:
            raise NotFoundError

        song_doc = SongDocument.get(id=existing_entry["_id"])
        song_doc.update(
            lyrics_text=lyrics_text, lyrics_translation=lyrics_translation_text
        )
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR % ("lyrics", SearchIndexEntryTypes.SONG, instance_id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "lyrics_update_signal",
                SearchIndexEntryTypes.SONG,
                song.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.SONG, instance_id)
        logger.error(e)
