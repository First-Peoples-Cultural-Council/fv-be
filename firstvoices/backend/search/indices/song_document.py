import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Keyword, Text

from backend.models import Lyric, Song
from backend.search.indices.base_document import BaseDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_SONG_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_object_from_index
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
def update_song_index(sender, instance, **kwargs):
    # add song to es index
    try:
        existing_entry = get_object_from_index(ELASTICSEARCH_SONG_INDEX, instance.id)
        # todo: verify each field is updated
        lyrics_text = ""
        lyrics_translation_text = ""

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
    except ConnectionError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(ES_CONNECTION_ERROR % (SearchIndexEntryTypes.SONG, instance.id))
        logger.error(e)
    except NotFoundError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.SONG,
            instance.id,
        )
        logger.warning(e)


@receiver(post_delete, sender=Lyric)
@receiver(post_save, sender=Lyric)
def update_lyrics(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    song = instance.song

    lyrics_text = ""
    lyrics_translation_text = ""

    try:
        existing_entry = get_object_from_index(ELASTICSEARCH_SONG_INDEX, song.id)
        if not existing_entry:
            raise NotFoundError

        song_doc = SongDocument.get(id=existing_entry["_id"])
        song_doc.update(
            lyrics_text=lyrics_text, lyrics_translation=lyrics_translation_text
        )
    except ConnectionError:
        logger.error(ES_CONNECTION_ERROR % (SearchIndexEntryTypes.SONG, instance.id))
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "lyrics_update_signal",
                SearchIndexEntryTypes.SONG,
                song.id,
            )
        )
