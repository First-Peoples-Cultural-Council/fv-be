from backend.search_indexes.dictionary_documents import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)


def hydrate_objects(raw_objects):
    complete_objects = []

    for obj in raw_objects:
        # todo: use _type instead of _index
        # DictionaryEntry
        if obj["_index"] == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            complete_object = {
                "id": obj["_id"],
                "score": obj["_score"],
                "title": obj["_source"]["title"],
                # "translation": obj["_source"]["translation"] # todo: to be added
            }

        complete_objects.append(complete_object)

    return complete_objects
