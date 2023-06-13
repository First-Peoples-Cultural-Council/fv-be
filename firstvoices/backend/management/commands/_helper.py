from django.core.paginator import Paginator
from elasticsearch.exceptions import NotFoundError

from backend.models.dictionary import DictionaryEntry
from backend.search.indices.dictionary_entry_document import dictionary_entries

ENTRIES_PER_PAGE = 100


def rebuild_index(index, index_document):
    # Delete index
    delete_index(index)

    # Initialize new index
    index_document.init()

    # Add documents
    if index == dictionary_entries:
        add_dictionary_entries_to_index()
    # Songs and stories to be added later


def delete_index(index):
    try:
        index.delete()
    except NotFoundError:
        print("Current index not found for deletion. Creating a new index.")


def add_dictionary_entries_to_index():
    # Iterate over dictionary entries
    queryset = DictionaryEntry.objects.all()
    paginator = Paginator(queryset, ENTRIES_PER_PAGE)
    total_pages = paginator.num_pages

    # Loop through each page
    for page_number in range(1, total_pages + 1):
        page_objects = paginator.page(page_number)

        # Loop through each object on the current page
        for entry in page_objects:
            print(entry)
            # Add dictionary entry to index
            # translations_text, part_of_speech_text = get_translation_and_part_of_speech_text(instance)
            # notes_text = get_notes_text(instance)
            # index_entry = DictionaryEntryDocument(
            #     document_id=entry.id,
            #     site_slug=entry.site.slug,
            #     title=entry.title,
            #     type=entry.type,
            #     translation=translations_text,
            #     part_of_speech=part_of_speech_text,
            #     note=notes_text,
            # )
