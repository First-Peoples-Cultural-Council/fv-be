import logging

from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Search

from backend.models import StoryPage
from backend.search.utils.constants import ES_CONNECTION_ERROR, ES_NOT_FOUND_ERROR
from firstvoices.settings import ELASTICSEARCH_LOGGER


def get_object_from_index(index, document_type, document_id):
    try:
        return search_by_id(document_id, index)
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


def search_by_id(document_id, index):
    s = Search(index=index).params(request_timeout=10)
    response = s.query("match", document_id=document_id).execute()
    hits = response["hits"]["hits"]
    return hits[0] if hits else None


def get_object_by_id(objects, object_id):
    # Function to find and return database object from list of objects
    filtered_objects = [
        obj for obj in objects if str(obj.id) == str(object_id) or obj.id == object_id
    ]

    if filtered_objects:
        return filtered_objects[0]

    raise KeyError(f"Object not found in db. id: {object_id}")


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
    pages = StoryPage.objects.filter(story=story_instance)
    page_text = list(pages.values_list("text", flat=True))
    page_translation = list(pages.values_list("translation", flat=True))

    return page_text, page_translation
