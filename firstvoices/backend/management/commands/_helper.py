from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections

from backend.models.dictionary import DictionaryEntry
from backend.search.indices.dictionary_entry_document import (
    DictionaryEntryDocument,
    dictionary_entries,
)
from backend.search.utils.object_utils import (
    get_notes_text,
    get_translation_and_part_of_speech_text,
)


def rebuild_index(index, index_document):
    es = connections.get_connection()

    # Delete index
    delete_index(index)

    # Initialize new index
    index_document.init()

    # Add documents
    if index == dictionary_entries:
        bulk(es, dictionary_entry_iterator())

    # Songs and stories to be added later


def delete_index(index):
    try:
        index.delete()
    except NotFoundError:
        print("Current index not found for deletion. Creating a new index.")


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
