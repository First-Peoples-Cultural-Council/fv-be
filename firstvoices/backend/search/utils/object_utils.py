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
        if obj["_index"] == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            dictionary_search_results_ids.append(obj["_source"]["document_id"])

    # Fetching objects from the database
    dictionary_objects = list(
        DictionaryEntry.objects.filter(
            id__in=dictionary_search_results_ids
        ).prefetch_related("translation_set")
    )

    for obj in search_results:
        # Handling DictionaryEntry objects
        if obj["_index"] == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
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
                            "site_slug": obj["_source"]["site_slug"],
                        },
                    ).data,
                }
            )

    return complete_objects
