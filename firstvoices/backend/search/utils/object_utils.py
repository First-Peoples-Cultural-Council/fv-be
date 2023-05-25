from backend.models.dictionary import DictionaryEntry
from backend.search.indices.dictionary_entry_document import (
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

            # related audio and other required fields to be added after discussion

            # Translations
            db_object = (
                DictionaryEntry.objects.filter(id=obj["_id"])
                .prefetch_related("translation_set")
                .first()
            )
            if db_object:
                translation_entries = db_object.translation_set.all()
                translations = []
                if len(translation_entries):
                    for translation in translation_entries:
                        translations.append(
                            {"id": translation.id, "text": translation.text}
                        )
                complete_object["translations"] = translations

        complete_objects.append(complete_object)

    return complete_objects
