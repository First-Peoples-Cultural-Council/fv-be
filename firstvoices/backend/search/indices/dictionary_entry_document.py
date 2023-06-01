import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Document, Index, Keyword, Text

from backend.models.dictionary import DictionaryEntry, Translation
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG, ELASTICSEARCH_LOGGER

ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entry"

# Defining index and settings
dictionary_entries = Index(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX)
dictionary_entries.settings(
    number_of_shards=ELASTICSEARCH_DEFAULT_CONFIG["shards"],
    number_of_replicas=ELASTICSEARCH_DEFAULT_CONFIG["replicas"],
)


@dictionary_entries.document
class DictionaryEntryDocument(Document):
    _id = Text()
    title = Text(analyzer="standard", ignore_above=256)
    type = Keyword()
    translation = Text(analyzer="standard", ignore_above=256)

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX


# Signal to update the entry in index
@receiver(post_save, sender=DictionaryEntry)
def update_index(sender, instance, **kwargs):
    # Add document to es index
    try:
        index_entry = DictionaryEntryDocument(
            _id=instance.id, title=instance.title, type=instance.type
        )
        index_entry.save()
    except ConnectionError:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            f"Elasticsearch server down. Document could not be updated in index. document id: {instance.id}"
        )


# Delete entry from index
@receiver(post_delete, sender=DictionaryEntry)
def delete_from_index(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        index_entry = DictionaryEntryDocument.get(id=instance.id)
        index_entry.delete()
    except ConnectionError:
        logger.warning(
            f"Elasticsearch server down. Documents could not be deleted in index. document id: {instance.id}"
        )
    except NotFoundError:
        logger.warning(
            f"Indexed document not found. Cannot delete from index. document id: {instance.id}"
        )


# Translation update
@receiver(post_save, sender=Translation)
def update_translation(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entry = instance.dictionary_entry

    try:
        dictionary_entry_doc = DictionaryEntryDocument.get(id=dictionary_entry.id)
        dictionary_entry_doc.update(translation=instance.text)
    except ConnectionError:
        logger.warning(
            f"Elasticsearch server down. Translation could not be updated in index. document id: {instance.id}"
        )
    except NotFoundError:
        logger.warning(
            f"Indexed document not found. Cannot updated dictionary_entry with translation. "
            f"document id: {dictionary_entry.id}"
        )


# Translation update
@receiver(post_delete, sender=Translation)
def delete_translation(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entry = instance.dictionary_entry

    try:
        dictionary_entry_doc = DictionaryEntryDocument.get(id=dictionary_entry.id)
        dictionary_entry_doc.update(translation=None)
    except ConnectionError:
        logger.warning(
            f"Elasticsearch server down. Translation could not be updated in index. document id: {instance.id}"
        )
    except NotFoundError:
        logger.warning(
            f"Indexed document not found. Cannot remove translation from dictionary_entry. "
            f"document id: {dictionary_entry.id}"
        )
