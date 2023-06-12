import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Document, Index, Keyword, Text

from backend.models.dictionary import DictionaryEntry, Note, Translation
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_object_from_index
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG, ELASTICSEARCH_LOGGER

# Defining index and settings
dictionary_entries = Index(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX)
dictionary_entries.settings(
    number_of_shards=ELASTICSEARCH_DEFAULT_CONFIG["shards"],
    number_of_replicas=ELASTICSEARCH_DEFAULT_CONFIG["replicas"],
)


@dictionary_entries.document
class DictionaryEntryDocument(Document):
    # generic fields, will be moved to a base search document once we have songs and stories
    document_id = Text()
    site_slug = Keyword()
    full_text_search_field = Text()

    # Dictionary Related fields
    type = Keyword()
    title = Text(analyzer="standard", copy_to="full_text_search_field")
    translation = Text(analyzer="standard", copy_to="full_text_search_field")
    note = Text(copy_to="full_text_search_field")
    part_of_speech = Text(copy_to="full_text_search_field")

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX


# Signal to update the entry in index
@receiver(post_save, sender=DictionaryEntry)
def update_index(sender, instance, **kwargs):
    # Add document to es index
    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, instance.id
        )
        if existing_entry:
            # Check if object is already indexed, then update
            index_entry = DictionaryEntryDocument.get(id=existing_entry["_id"])
            index_entry.update(
                site_slug=instance.site.slug, title=instance.title, type=instance.type
            )
        else:
            # Create new entry if it doesnt exists
            index_entry = DictionaryEntryDocument(
                document_id=instance.id,
                site_slug=instance.site.slug,
                title=instance.title,
                type=instance.type,
            )
            index_entry.save()
    except ConnectionError:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_CONNECTION_ERROR % (SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
        )


# Delete entry from index
@receiver(post_delete, sender=DictionaryEntry)
def delete_from_index(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, instance.id
        )
        index_entry = DictionaryEntryDocument.get(id=existing_entry["_id"])
        index_entry.delete()
    except ConnectionError:
        logger.warning(
            ES_CONNECTION_ERROR % (SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
        )


# Translation update
@receiver(post_delete, sender=Translation)
@receiver(post_save, sender=Translation)
def update_translation(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entry = instance.dictionary_entry
    translation_set = dictionary_entry.translation_set.all()

    translations_text = []
    part_of_speech_titles = []

    for t in translation_set:
        translations_text.append(t.text)
        if t.part_of_speech:
            part_of_speech_titles.append(t.part_of_speech.title)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, dictionary_entry.id
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(
            translation=" ".join(translations_text),
            part_of_speech=" ".join(part_of_speech_titles),
        )
    except ConnectionError:
        logger.warning(
            ES_CONNECTION_ERROR % (SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
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
    notes_set = dictionary_entry.note_set.all()

    notes_text = []

    for note in notes_set:
        notes_text.append(note.text)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, dictionary_entry.id
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(note=" ".join(notes_text))
    except ConnectionError:
        logger.warning(
            ES_CONNECTION_ERROR % (SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
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
