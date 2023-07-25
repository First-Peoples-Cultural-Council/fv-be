import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Keyword, Text

from backend.models.dictionary import (
    Acknowledgement,
    DictionaryEntry,
    DictionaryEntryCategory,
    Note,
    Translation,
)
from backend.search.indices.base_document import BaseDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
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


class DictionaryEntryDocument(BaseDocument):
    # text search fields
    title = Text(fields={"raw": Keyword()}, copy_to="primary_language_search_fields")
    translation = Text(copy_to="primary_translation_search_fields")
    note = Text(copy_to="other_translation_search_fields")
    acknowledgement = Text(copy_to="other_translation_search_fields")

    # filter and sorting
    type = Keyword()
    custom_order = Keyword()
    categories = Keyword()

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX


# Signal to update the entry in index
@receiver(post_save, sender=DictionaryEntry)
def update_dictionary_entry_index(sender, instance, **kwargs):
    # Add document to es index
    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, "dictionary_entry", instance.id
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
            )
            index_entry.save()
    except ConnectionError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            ES_CONNECTION_ERROR
            % ("dictionary_entry", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
        )
        logger.error(e)
    except NotFoundError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.DICTIONARY_ENTRY,
            instance.id,
        )
        logger.warning(e)


# Delete entry from index
@receiver(post_delete, sender=DictionaryEntry)
def delete_from_index(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, "dictionary_entry", instance.id
        )
        if existing_entry:
            index_entry = DictionaryEntryDocument.get(id=existing_entry["_id"])
            index_entry.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("dictionary_entry", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
        )


# Translation update
@receiver(post_delete, sender=Translation)
@receiver(post_save, sender=Translation)
def update_translation(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entry = instance.dictionary_entry

    translations_text = get_translation_text(dictionary_entry)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "dictionary_entry",
            dictionary_entry.id,
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(translation=translations_text)
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("translation", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "translation_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry.id,
            )
        )


# Note update
@receiver(post_delete, sender=Note)
@receiver(post_save, sender=Note)
def update_notes(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entry = instance.dictionary_entry
    notes_text = get_notes_text(dictionary_entry)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "dictionary_entry",
            dictionary_entry.id,
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(note=notes_text)
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("notes", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "notes_update_signal",
                SearchIndexEntryTypes.DICTIONARY_ENTRY,
                dictionary_entry.id,
            )
        )


# Acknowledgement update
@receiver(post_delete, sender=Acknowledgement)
@receiver(post_save, sender=Acknowledgement)
def update_acknowledgement(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entry = instance.dictionary_entry
    acknowledgements_text = get_acknowledgements_text(dictionary_entry)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "dictionary_entry",
            dictionary_entry.id,
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(acknowledgement=acknowledgements_text)
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("acknowledgements", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
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


# Category update
@receiver(post_save, sender=DictionaryEntryCategory)
@receiver(post_delete, sender=DictionaryEntryCategory)
def update_categories(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entry = instance.dictionary_entry
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
        dictionary_entry_doc.update(categories=categories)
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("categories", SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
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
