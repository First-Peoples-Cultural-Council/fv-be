from backend.models.dictionary import DictionaryEntry
from backend.search.indices.dictionary_entry_document import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)
from backend.search.utils.constants import SearchIndexEntryTypes
from backend.serializers.dictionary_serializers import DictionaryEntryDetailSerializer


def get_object(objects, object_id):
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
        if obj["_index"] == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            dictionary_search_results_ids.append(obj["_id"])

    # Fetching objects from the database
    dictionary_objects = list(
        DictionaryEntry.objects.filter(
            id__in=dictionary_search_results_ids
        ).prefetch_related("translation_set")
    )

    for obj in search_results:
        # Handling DictionaryEntry objects
        if obj["_index"] == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            dictionary_entry = get_object(dictionary_objects, obj["_id"])
            request.parser_context["kwargs"]["site_slug"] = dictionary_entry.site.slug

            # Serializing and adding the object to complete_objects
            complete_objects.append(
                {
                    "_id": obj["_id"],
                    "score": obj["_score"],
                    "type": SearchIndexEntryTypes.DICTIONARY_ENTRY,
                    "entry": DictionaryEntryDetailSerializer(
                        dictionary_entry,
                        context={"request": request, "view": "custom_search"},
                    ).data,
                }
            )

    return complete_objects
