from backend.search_indices.dictionary_entry_document import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)


def hydrate_objects(raw_objects):
    """
    Adding required properties to raw objects returned form elastic-search.
    """
    complete_objects = []

    for obj in raw_objects:
        complete_object = {
            "id": obj["_id"],
            "score": obj["_score"],
            "title": obj["_source"]["title"],
        }

        # DictionaryEntry
        if obj["_index"] == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            # Adding type
            complete_object["type"] = obj["_source"]["type"]

            # related audio, url, translation and other required fields to be added after discussion

        complete_objects.append(complete_object)

    return complete_objects
