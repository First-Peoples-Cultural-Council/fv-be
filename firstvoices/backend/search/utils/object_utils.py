import logging

from elasticsearch_dsl import Search

from backend.models.dictionary import DictionaryEntry
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ES_CONNECTION_ERROR,
    SearchIndexEntryTypes,
)
from backend.serializers.dictionary_serializers import DictionaryEntryDetailSerializer
from firstvoices.settings import ELASTICSEARCH_LOGGER


def get_object_from_index(index, document_id):
    try:
        s = Search(index=index)
        response = s.query("match", document_id=document_id).execute()
        hits = response["hits"]["hits"]

        return hits[0] if hits else None
    except ConnectionError:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_CONNECTION_ERROR % (SearchIndexEntryTypes.DICTIONARY_ENTRY, document_id)
        )


def get_object_by_id(objects, object_id):
    # Function to find and return database object from list of objects
    filtered_objects = [obj for obj in objects if str(obj.id) == object_id]

    if len(filtered_objects):
        return filtered_objects[0]
    else:
        return None


def hydrate_objects(search_results, request):
    """
    To enhance the raw objects returned from ElasticSearch, we add the necessary properties.
    First, we segregate all the IDs from the search results into separate lists based on their respective models.
    Next, we query the database using these IDs. Once we retrieve the objects from the database, we iterate over the
    search results and include a serialized object for each entry.
    """
    complete_objects = []
    dictionary_search_results_ids = []

    # Separating object IDs into lists based on their data types
    for obj in search_results:
        if ELASTICSEARCH_DICTIONARY_ENTRY_INDEX in obj["_index"]:
            dictionary_search_results_ids.append(obj["_source"]["document_id"])

    # Fetching objects from the database
    dictionary_objects = list(
        DictionaryEntry.objects.filter(
            id__in=dictionary_search_results_ids
        ).prefetch_related("translation_set")
    )

    for obj in search_results:
        # Handling DictionaryEntry objects
        if ELASTICSEARCH_DICTIONARY_ENTRY_INDEX in obj["_index"]:
            dictionary_entry = get_object_by_id(
                dictionary_objects, obj["_source"]["document_id"]
            )

            # Serializing and adding the object to complete_objects
            complete_objects.append(
                {
                    "_id": obj["_id"],
                    "score": obj["_score"],
                    "type": SearchIndexEntryTypes.DICTIONARY_ENTRY,
                    "entry": DictionaryEntryDetailSerializer(
                        dictionary_entry,
                        context={
                            "request": request,
                            "view": "search",
                            "site_slug": dictionary_entry.site.slug,
                        },
                    ).data,
                }
            )

    return complete_objects


def get_translation_and_part_of_speech_text(dictionary_entry_instance):
    translation_set = dictionary_entry_instance.translation_set.all()
    translations = []
    part_of_speech_titles = []
    for t in translation_set:
        translations.append(t.text)
        if t.part_of_speech:
            part_of_speech_titles.append(t.part_of_speech.title)

    translations_text = " ".join(translations)
    part_of_speech_text = " ".join(part_of_speech_titles)

    return translations_text, part_of_speech_text


def get_notes_text(dictionary_entry_instance):
    notes_set = dictionary_entry_instance.note_set.all()
    notes_text = []
    for note in notes_set:
        notes_text.append(note.text)
    return " ".join(notes_text)


def get_categories_ids(dictionary_entry_instance):
    categories_set = dictionary_entry_instance.categories.all()
    categories_list = []
    for category in categories_set:
        categories_list.append(str(category.id))
    return categories_list
