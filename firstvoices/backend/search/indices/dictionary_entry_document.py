import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Boolean, Document, Integer, Keyword, Text

from backend.models.dictionary import (
    DictionaryEntry,
    DictionaryEntryCategory,
    Note,
    Translation,
)
from backend.models.sites import Site
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import (
    get_categories_ids,
    get_notes_text,
    get_object_from_index,
    get_translation_and_part_of_speech_text,
)
from firstvoices.settings import ELASTICSEARCH_LOGGER


class DictionaryEntryDocument(Document):
    # generic fields, will be moved to a base search document once we have songs and stories
    document_id = Text()
    site_id = Keyword()
    site_visibility = Integer()
    full_text_search_field = Text()
    exclude_from_games = Boolean()
    exclude_from_kids = Boolean()
    visibility = Integer()

    # Dictionary Related fields
    type = Keyword()
    custom_order = Keyword()
    title = Text(analyzer="standard", copy_to="full_text_search_field")
    translation = Text(analyzer="standard", copy_to="full_text_search_field")
    note = Text(copy_to="full_text_search_field")
    part_of_speech = Text(copy_to="full_text_search_field")
    categories = Keyword()

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
        (
            translations_text,
            part_of_speech_text,
        ) = get_translation_and_part_of_speech_text(instance)
        notes_text = get_notes_text(instance)
        categories = get_categories_ids(instance)

        if existing_entry:
            # Check if object is already indexed, then update
            index_entry = DictionaryEntryDocument.get(id=existing_entry["_id"])
            index_entry.update(
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                title=instance.title,
                type=instance.type,
                translation=translations_text,
                part_of_speech=part_of_speech_text,
                note=notes_text,
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
                part_of_speech=part_of_speech_text,
                note=notes_text,
                custom_order=instance.custom_order,
                categories=categories,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=instance.visibility,
            )
            index_entry.save()
    except ConnectionError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_CONNECTION_ERROR % (SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
        )
        logger.warning(e)
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

    translations_text, part_of_speech_text = get_translation_and_part_of_speech_text(
        dictionary_entry
    )

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, dictionary_entry.id
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(
            translation=translations_text,
            part_of_speech=part_of_speech_text,
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
    notes_text = get_notes_text(dictionary_entry)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, dictionary_entry.id
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(note=notes_text)
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


# If a site is deleted, delete all docs from index related to site
@receiver(post_delete, sender=Site)
def delete_related_docs(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entries_set = instance.dictionaryentry_set.all()

    for dictionary_entry in dictionary_entries_set:
        try:
            existing_entry = get_object_from_index(
                ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, dictionary_entry.id
            )
            if not existing_entry:
                raise NotFoundError

            dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
            dictionary_entry_doc.delete()
        except ConnectionError:
            logger.warning(
                ES_CONNECTION_ERROR
                % (SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
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


@receiver(post_save, sender=DictionaryEntryCategory)
@receiver(post_delete, sender=DictionaryEntryCategory)
def update_categories(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entry = instance.dictionary_entry
    categories = get_categories_ids(dictionary_entry)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, dictionary_entry.id
        )
        if not existing_entry:
            raise NotFoundError

        dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
        dictionary_entry_doc.update(categories=categories)
    except ConnectionError:
        logger.warning(
            ES_CONNECTION_ERROR % (SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
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


# If a site's visibility is changed, update all docs from index related to site
@receiver(post_save, sender=Site)
def update_document_visibility(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    dictionary_entries_set = instance.dictionaryentry_set.all()

    for dictionary_entry in dictionary_entries_set:
        try:
            existing_entry = get_object_from_index(
                ELASTICSEARCH_DICTIONARY_ENTRY_INDEX, dictionary_entry.id
            )
            if not existing_entry:
                raise NotFoundError

            dictionary_entry_doc = DictionaryEntryDocument.get(id=existing_entry["_id"])
            dictionary_entry_doc.update(site_visibility=instance.visibility)
        except ConnectionError:
            logger.warning(
                ES_CONNECTION_ERROR
                % (SearchIndexEntryTypes.DICTIONARY_ENTRY, instance.id)
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
