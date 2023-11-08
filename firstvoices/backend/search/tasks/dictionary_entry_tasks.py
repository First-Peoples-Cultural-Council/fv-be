import logging

from celery import shared_task
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Index

from backend.models.dictionary import DictionaryEntry, DictionaryEntryCategory
from backend.search.documents import DictionaryEntryDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    RETRY_ON_CONFLICT,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import (
    get_acknowledgements_text,
    get_categories_ids,
    get_notes_text,
    get_object_from_index,
    get_translation_text,
)
from firstvoices.settings import ELASTICSEARCH_LOGGER


@shared_task
def update_dictionary_entry_index(instance_id, **kwargs):
    # Add document to es index
    try:
        instance = DictionaryEntry.objects.get(id=instance_id)
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, "dictionary_entry", instance_id
        )
        translations_text = get_translation_text(instance)
        notes_text = get_notes_text(instance)
        categories = get_categories_ids(instance)
        acknowledgements_text = get_acknowledgements_text(instance)

        if existing_entry:
            # Check if object is already indexed, then update
            index_entry = DictionaryEntryDocument.get(id=existing_entry["_id"])
            index_entry.update(
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                title=instance.title,
                type=instance.type,
                translation=translations_text,
                note=notes_text,
                acknowledgement=acknowledgements_text,
                custom_order=instance.custom_order,
                categories=categories,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=instance.visibility,
                retry_on_conflict=RETRY_ON_CONFLICT,
                has_audio=instance.related_audio.exists(),
                has_video=instance.related_videos.exists(),
                has_image=instance.related_images.exists(),
            )
        else:
            # Create new entry if it doesn't exist
            index_entry = DictionaryEntryDocument(
                document_id=str(instance.id),
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                title=instance.title,
                type=instance.type,
                translation=translations_text,
                note=notes_text,
                acknowledgement=acknowledgements_text,
                custom_order=instance.custom_order,
                categories=categories,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=instance.visibility,
                has_audio=instance.related_audio.exists(),
                has_video=instance.related_videos.exists(),
                has_image=instance.related_images.exists(),
            )
            index_entry.save()
        # Refresh the index to ensure the index is up-to-date for related field signals
        dict_index = Index(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX)
        dict_index.refresh()
    except ConnectionError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            ES_CONNECTION_ERROR
            % ("dictionary_entry", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id)
        )
        logger.error(e)
    except NotFoundError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.DICTIONARY_ENTRY,
            instance_id,
        )
        logger.warning(e)
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            type(e).__name__, SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id
        )
        logger.error(e)


@shared_task
def delete_from_index(instance_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, "dictionary_entry", instance_id
        )
        if existing_entry:
            index_entry = DictionaryEntryDocument.get(id=existing_entry["_id"])
            index_entry.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("dictionary_entry", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id)
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            type(e).__name__, SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id
        )
        logger.error(e)


@shared_task
def update_translation(instance_id, dictionary_entry_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    # Set dictionary entry and sub-model text. If it doesn't exist due to deletion, warn and return.
    try:
        dictionary_entry = DictionaryEntry.objects.get(id=dictionary_entry_id)
        translations_text = get_translation_text(dictionary_entry)
    except DictionaryEntry.DoesNotExist:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "translation_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry_id,
            )
        )
        return

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "dictionary_entry",
            dictionary_entry_id,
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(
            translation=translations_text, retry_on_conflict=RETRY_ON_CONFLICT
        )
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("translation", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "translation_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry_id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            type(e).__name__, SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id
        )
        logger.error(e)


@shared_task
def update_notes(instance_id, dictionary_entry_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    # Set dictionary entry and sub-model text. If it doesn't exist due to deletion, warn and return.
    try:
        dictionary_entry = DictionaryEntry.objects.get(id=dictionary_entry_id)
        notes_text = get_notes_text(dictionary_entry)
    except DictionaryEntry.DoesNotExist:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "notes_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry_id,
            )
        )
        return

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "dictionary_entry",
            dictionary_entry_id,
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(
            note=notes_text, retry_on_conflict=RETRY_ON_CONFLICT
        )
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("notes", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "notes_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry_id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            type(e).__name__, SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id
        )
        logger.error(e)


@shared_task
def update_acknowledgements(instance_id, dictionary_entry_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    # Set dictionary entry and sub-model text. If it doesn't exist due to deletion, warn and return.
    try:
        dictionary_entry = DictionaryEntry.objects.get(id=dictionary_entry_id)
        acknowledgements_text = get_acknowledgements_text(dictionary_entry)
    except DictionaryEntry.DoesNotExist:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "acknowledgements_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry_id,
            )
        )
        return

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "dictionary_entry",
            dictionary_entry_id,
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(
            acknowledgement=acknowledgements_text, retry_on_conflict=RETRY_ON_CONFLICT
        )
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("acknowledgements", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "acknowledgements_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            type(e).__name__, SearchIndexEntryTypes.DICTIONARY_ENTRY, instance_id
        )
        logger.error(e)


@shared_task
def update_categories(instance_id, **kwargs):
    if DictionaryEntryCategory.objects.filter(id=instance_id).exists():
        instance = DictionaryEntryCategory.objects.get(id=instance_id)
        update_dictionary_entry_index_categories(instance.dictionary_entry)


@shared_task
def update_categories_m2m(instance_id, **kwargs):
    if DictionaryEntryCategory.objects.filter(id=instance_id).exists():
        instance = DictionaryEntryCategory.objects.get(id=instance_id)
        update_dictionary_entry_index_categories(instance)


def update_dictionary_entry_index_categories(dictionary_entry):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    categories = get_categories_ids(dictionary_entry)
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
            categories=categories, retry_on_conflict=RETRY_ON_CONFLICT
        )
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % (
                "categories",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry.id,
            )
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "categories_update_signal",
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
