import logging

from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Search

from backend.models import DictionaryEntry, Song, Story
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
)
from backend.serializers.dictionary_serializers import DictionaryEntryDetailSerializer
from backend.serializers.song_serializers import SongSerializer
from backend.serializers.story_serializers import StorySerializer
from firstvoices.settings import ELASTICSEARCH_LOGGER


def get_object_from_index(index, document_type, document_id):
    try:
        s = Search(index=index).params(request_timeout=10)
        response = s.query("match", document_id=document_id).execute()
        hits = response["hits"]["hits"]

        return hits[0] if hits else None
    except ConnectionError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(ES_CONNECTION_ERROR, document_type, index, document_id)
        logger.error(e)
        raise e
    except NotFoundError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "query",
            index,
            document_id,
        )
        logger.warning(e)

    return None


def get_object_by_id(objects, object_id):
    # Function to find and return database object from list of objects
    filtered_objects = [
        obj for obj in objects if str(obj.id) == object_id or obj.id == object_id
    ]

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
    song_search_results_ids = []
    story_search_results_ids = []

    # Separating object IDs into lists based on their data types
    for obj in search_results:
        if ELASTICSEARCH_DICTIONARY_ENTRY_INDEX in obj["_index"]:
            dictionary_search_results_ids.append(obj["_source"]["document_id"])
        elif ELASTICSEARCH_SONG_INDEX in obj["_index"]:
            song_search_results_ids.append(obj["_source"]["document_id"])
        elif ELASTICSEARCH_STORY_INDEX in obj["_index"]:
            story_search_results_ids.append(obj["_source"]["document_id"])

    # Fetching objects from the database
    dictionary_objects = list(
        DictionaryEntry.objects.filter(
            id__in=dictionary_search_results_ids
        ).prefetch_related("translation_set")
    )
    song_objects = list(
        Song.objects.filter(id__in=song_search_results_ids).prefetch_related("lyrics")
    )
    story_objects = list(
        Story.objects.filter(id__in=story_search_results_ids).prefetch_related("pages")
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
                    "score": obj["_score"],
                    "type": dictionary_entry.type.lower(),  # 'word' or 'phrase' instead of 'dictionary_entry'
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
        elif ELASTICSEARCH_SONG_INDEX in obj["_index"]:
            song = get_object_by_id(song_objects, obj["_source"]["document_id"])

            # Serializing and adding the object to complete_objects
            complete_objects.append(
                {
                    "score": obj["_score"],
                    "type": "song",
                    "entry": SongSerializer(
                        song,
                        context={
                            "request": request,
                            "view": "search",
                            "site_slug": song.site.slug,
                        },
                    ).data,
                }
            )
        elif ELASTICSEARCH_STORY_INDEX in obj["_index"]:
            story = get_object_by_id(story_objects, obj["_source"]["document_id"])

            # Serializing and adding the object to complete_objects
            complete_objects.append(
                {
                    "score": obj["_score"],
                    "type": "story",
                    "entry": StorySerializer(
                        story,
                        context={
                            "request": request,
                            "view": "search",
                            "site_slug": story.site.slug,
                        },
                    ).data,
                }
            )

    return complete_objects


def get_translation_text(dictionary_entry_instance):
    translations = list(
        dictionary_entry_instance.translation_set.values_list("text", flat=True)
    )
    return " ".join(translations)


def get_acknowledgements_text(dictionary_entry_instance):
    acknowledgements = list(
        dictionary_entry_instance.acknowledgement_set.values_list("text", flat=True)
    )
    return " ".join(acknowledgements)


def get_notes_text(dictionary_entry_instance):
    notes = list(dictionary_entry_instance.note_set.values_list("text", flat=True))
    return " ".join(notes)


def get_categories_ids(dictionary_entry_instance):
    return [
        str(category_id)
        for category_id in dictionary_entry_instance.categories.values_list(
            "id", flat=True
        )
    ]


def get_lyrics(song_instance):
    lyrics = list(song_instance.lyrics.values_list("text", flat=True))
    lyrics_translation = list(
        song_instance.lyrics.values_list("translation", flat=True)
    )

    return lyrics, lyrics_translation


def get_page_info(story_instance):
    page_text = list(story_instance.pages.values_list("text", flat=True))
    page_translation = list(story_instance.pages.values_list("translation", flat=True))

    return page_text, page_translation
