import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError, NotFoundError

from backend.models.sites import Site
from backend.search.indices import DictionaryEntryDocument, SongDocument, StoryDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_object_from_index
from firstvoices.celery import link_error_handler
from firstvoices.settings import ELASTICSEARCH_LOGGER


# If a site's visibility is changed, update all docs from index related to site
@receiver(pre_save, sender=Site)
def request_update_document_visibility(sender, instance, **kwargs):
    if instance.id is None:
        # New site, don't do anything
        return

    try:
        original_site = Site.objects.get(id=instance.id)
    except ObjectDoesNotExist:
        # New site or deleted, don't do anything
        return

    if original_site.visibility != instance.visibility:
        update_document_visibility.apply_async(
            (instance.id, instance.visibility), link_error=link_error_handler.s()
        )


@shared_task
def update_document_visibility(instance_id, instance_visibility, **kwargs):
    instance = Site.objects.get(id=instance_id)
    dictionary_entries_set = instance.dictionaryentry_set.all()
    songs_set = instance.song_set.all()
    stories_set = instance.story_set.all()

    # Updating dictionary_entries visibility
    for dictionary_entry in dictionary_entries_set:
        update_dictionary_entry_visibility(dictionary_entry, instance_visibility)

    # Updating songs visibility
    for song in songs_set:
        update_song_visibility(song, instance_visibility)

    # updating story visibility
    for story in stories_set:
        update_story_visibility(story, instance_visibility)


# If a site is deleted, delete all docs from index related to site
@receiver(post_delete, sender=Site)
def request_delete_related_docs(sender, instance, **kwargs):
    if Site.objects.filter(id=instance.id).exists():
        delete_related_docs.apply_async(
            (instance.id,), link_error=link_error_handler.s()
        )


@shared_task
def delete_related_docs(instance_id, **kwargs):
    instance = Site.objects.get(id=instance_id)
    dictionary_entries_set = instance.dictionaryentry_set.all()
    songs_set = instance.song_set.all()
    stories_set = instance.story_set.all()

    # removing dictionary_entries related to the deleted site
    for dictionary_entry in dictionary_entries_set:
        remove_dictionary_entry_from_index(dictionary_entry)

    # removing songs related to the deleted site
    for song in songs_set:
        remove_song_from_index(song)

    # removing story related to the deleted site
    for story in stories_set:
        remove_story_from_index(story)


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
        dictionary_entry_doc.update(site_visibility=updated_visibility)
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
        song_doc.update(site_visibility=updated_visibility)
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
        story_doc.update(site_visibility=updated_visibility)
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
