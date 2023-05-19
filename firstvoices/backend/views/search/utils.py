from backend.search_indexes.dictionary_documents import (
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

            # Adding translation
            translations = []
            translation_set = obj["_source"]["translation_set"]
            if len(translation_set):
                for translation in translation_set:
                    translations.append(
                        {"id": translation["id"], "text": translation["text"]}
                    )
            complete_object["translations"] = translations

            # related audio, url, and other required fields to be added after discussion

        complete_objects.append(complete_object)

    return complete_objects
