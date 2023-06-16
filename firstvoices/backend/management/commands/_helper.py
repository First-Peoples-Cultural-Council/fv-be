from django.core.management import CommandError
from django.utils import timezone
from elasticsearch.helpers import bulk, errors
from elasticsearch_dsl import Index
from elasticsearch_dsl.connections import connections

from backend.models.dictionary import DictionaryEntry
from backend.search.indices.dictionary_entry_document import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    DictionaryEntryDocument,
)
from backend.search.utils.object_utils import (
    get_notes_text,
    get_translation_and_part_of_speech_text,
)
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG


def rebuild_index(index_name, index_document):
    es = connections.get_connection()

    # Get the latest index
    current_index = get_current_index(es, index_name)
    if current_index:
        # If current index present, try removing alias
        current_index.delete_alias(using=es, name=index_name, ignore=404)

    # Create new index with current timestamp
    current_timestamp = timezone.now().strftime("%Y_%m_%d_%H_%M_%S")
    new_index_name = index_name + "_" + current_timestamp
    new_index = Index(new_index_name)
    new_index.settings(
        number_of_shards=ELASTICSEARCH_DEFAULT_CONFIG["shards"],
        number_of_replicas=ELASTICSEARCH_DEFAULT_CONFIG["replicas"],
    )

    # adding document and alias
    new_index.document(index_document)
    new_index = add_alias(new_index, index_name)
    new_index.create()

    # Index all documents in this index
    try:
        if index_name == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            bulk(es, dictionary_entry_iterator())
    except errors.BulkIndexError as e:
        if "multiple indices" in str(e):
            raise CommandError(
                "There are multiple indices with same alias. Try clearing all indices and then "
                "rebuilding."
            )
    except Exception as e:
        # Any other exception due to which we are not able to build a new index or add documents to it
        # Attach alias back to current index so search keeps working
        add_alias(current_index, index_name)
        raise CommandError(
            "The following error occurred while indexing documents. Adding alias back to current index. "
            + str(e)
        )

    # Removing old index
    if current_index:
        current_index.delete(ignore=404)

    # Songs and stories to be added later


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


def dictionary_entry_iterator():
    queryset = DictionaryEntry.objects.all()
    for entry in queryset:
        (
            translations_text,
            part_of_speech_text,
        ) = get_translation_and_part_of_speech_text(entry)
        notes_text = get_notes_text(entry)
        index_entry = DictionaryEntryDocument(
            document_id=entry.id,
            site_slug=entry.site.slug,
            title=entry.title,
            type=entry.type,
            translation=translations_text,
            part_of_speech=part_of_speech_text,
            note=notes_text,
        )
        yield index_entry.to_dict(True)


def add_alias(index, index_name):
    if index_name == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
        index.aliases(dictionary_entries={})
    return index


def get_valid_index_name(mappings, index_name):
    if index_name in mappings:
        return index_name
    else:
        return None
