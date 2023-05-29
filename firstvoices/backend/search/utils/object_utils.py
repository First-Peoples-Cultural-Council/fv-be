from backend.models.dictionary import DictionaryEntry
from backend.search.indices.dictionary_entry_document import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)


def get_object(objects, id):
    # Function to return db object from list of objects
    filtered_objects = [obj for obj in objects if str(obj.id) == id]

    if len(filtered_objects):
        return filtered_objects[0]
    else:
        return None


def get_translations(dictionary_entry):
    translations = []
    translation_entries = dictionary_entry.translation_set.all()
    if len(translation_entries):
        for translation in translation_entries:
            translations.append({"id": translation.id, "text": translation.text})
    return translations


def hydrate_objects(search_results):
    """
    Adding required properties to raw objects returned form elastic-search.
    """
    complete_objects = []

    # Separating objects ids into lists according to their data types
    dictionary_search_results_ids = []

    for obj in search_results:
        if obj["_index"] == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            dictionary_search_results_ids.append(obj["_id"])

    # Fetch objects from db
    dictionary_objects = list(
        DictionaryEntry.objects.filter(
            id__in=dictionary_search_results_ids
        ).prefetch_related("translation_set")
    )

    for obj in search_results:
        complete_object = {
            "id": obj["_id"],
            "score": obj["_score"],
            "title": obj["_source"]["title"],
        }

        # DictionaryEntry
        if obj["_index"] == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            # Adding type
            dictionary_entry = get_object(dictionary_objects, obj["_id"])
            complete_object["type"] = dictionary_entry.type
            complete_object["translations"] = get_translations(dictionary_entry)

        complete_objects.append(complete_object)

    return complete_objects
