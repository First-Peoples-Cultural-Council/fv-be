import logging

from backend.models import DictionaryEntry, Image, Song, Story
from backend.models.media import Audio, Video
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_MEDIA_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
    TYPE_AUDIO,
    TYPE_IMAGE,
    TYPE_VIDEO,
)
from backend.search.utils.object_utils import get_object_by_id
from backend.serializers.dictionary_serializers import DictionaryEntryMinimalSerializer
from backend.serializers.media_serializers import (
    AudioSerializer,
    ImageMinimalSerializer,
    VideoMinimalSerializer,
)
from backend.serializers.song_serializers import SongMinimalSerializer
from backend.serializers.story_serializers import StoryMinimalSerializer
from firstvoices.settings import ELASTICSEARCH_LOGGER


def separate_object_ids(search_results):
    # Separate the mixed search results to fetch objects from db
    search_results_dict = {
        ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
        ELASTICSEARCH_SONG_INDEX: [],
        ELASTICSEARCH_STORY_INDEX: [],
        ELASTICSEARCH_MEDIA_INDEX: {
            TYPE_AUDIO: [],
            TYPE_IMAGE: [],
            TYPE_VIDEO: [],
        },
    }

    # Separating object IDs into lists based on their data types
    for obj in search_results:
        index = obj["_index"]
        doc_id = obj["_source"]["document_id"]
        doc_type = (
            obj["_source"]["type"]
            if index.startswith(ELASTICSEARCH_MEDIA_INDEX)
            else None
        )

        if index.startswith(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX):
            search_results_dict[ELASTICSEARCH_DICTIONARY_ENTRY_INDEX].append(doc_id)
        elif index.startswith(ELASTICSEARCH_SONG_INDEX):
            search_results_dict[ELASTICSEARCH_SONG_INDEX].append(doc_id)
        elif index.startswith(ELASTICSEARCH_STORY_INDEX):
            search_results_dict[ELASTICSEARCH_STORY_INDEX].append(doc_id)
        elif index.startswith(ELASTICSEARCH_MEDIA_INDEX) and doc_type:
            search_results_dict[ELASTICSEARCH_MEDIA_INDEX][doc_type].append(doc_id)

    return search_results_dict


def fetch_objects_from_database(
    id_list, model, select_related_fields=None, prefetch_fields=None, defer_fields=None
):
    objects = model.objects.filter(id__in=id_list)
    if select_related_fields:
        objects = objects.select_related(*select_related_fields)
    if prefetch_fields:
        objects = objects.prefetch_related(*prefetch_fields)
    if defer_fields:
        objects = objects.defer(*defer_fields)
    return objects


def hydrate_objects(search_results, request):
    """
    To enhance the raw objects returned from ElasticSearch, we add the necessary properties.
    First, we segregate all the IDs from the search results into separate lists based on their respective models.
    Next, we query the database using these IDs. Once we retrieve the objects from the database, we iterate over the
    search results and include a serialized object for each entry.
    """
    complete_objects = []
    search_results_dict = separate_object_ids(search_results)

    # Fetching objects from the database
    dictionary_objects = fetch_objects_from_database(
        search_results_dict[ELASTICSEARCH_DICTIONARY_ENTRY_INDEX],
        DictionaryEntry,
        select_related_fields=["site"],
        prefetch_fields=[
            "translation_set",
            "related_audio",
            "related_images",
            "related_audio__original",
            "related_audio__speakers",
            "related_images__original",
        ],
    )

    song_objects = fetch_objects_from_database(
        search_results_dict[ELASTICSEARCH_SONG_INDEX],
        Song,
        prefetch_fields=[
            "site",
            "related_images",
            "related_images__original",
        ],
    )

    story_objects = fetch_objects_from_database(
        search_results_dict[ELASTICSEARCH_STORY_INDEX],
        Story,
        select_related_fields=["site"],
        prefetch_fields=[
            "site",
            "related_images",
            "related_images__original",
        ],
    )

    audio_objects = fetch_objects_from_database(
        search_results_dict[ELASTICSEARCH_MEDIA_INDEX][TYPE_AUDIO],
        Audio,
        select_related_fields=["site"],
        prefetch_fields=["original", "site", "speakers"],
        defer_fields=["created_by_id", "last_modified_by_id", "last_modified"],
    )

    image_objects = fetch_objects_from_database(
        search_results_dict[ELASTICSEARCH_MEDIA_INDEX][TYPE_IMAGE],
        Image,
    )

    video_objects = fetch_objects_from_database(
        search_results_dict[ELASTICSEARCH_MEDIA_INDEX][TYPE_VIDEO],
        Video,
    )

    for obj in search_results:
        complete_object = {"searchResultId": obj["_id"], "score": obj["_score"]}

        try:
            # Serializing objects
            if ELASTICSEARCH_DICTIONARY_ENTRY_INDEX in obj["_index"]:
                dictionary_entry = get_object_by_id(
                    dictionary_objects, obj["_source"]["document_id"]
                )
                complete_object[
                    "type"
                ] = dictionary_entry.type.lower()  # 'word' or 'phrase'
                complete_object["entry"] = DictionaryEntryMinimalSerializer(
                    dictionary_entry,
                    context={"request": request},
                ).data

            elif ELASTICSEARCH_SONG_INDEX in obj["_index"]:
                song = get_object_by_id(song_objects, obj["_source"]["document_id"])
                complete_object["type"] = "song"
                complete_object["entry"] = SongMinimalSerializer(
                    song, context={"request": request}
                ).data

            elif ELASTICSEARCH_STORY_INDEX in obj["_index"]:
                story = get_object_by_id(story_objects, obj["_source"]["document_id"])
                complete_object["type"] = "story"
                complete_object["entry"] = StoryMinimalSerializer(
                    story, context={"request": request}
                ).data

            elif (
                ELASTICSEARCH_MEDIA_INDEX in obj["_index"]
                and obj["_source"]["type"] == TYPE_AUDIO
            ):
                audio = get_object_by_id(audio_objects, obj["_source"]["document_id"])
                complete_object["type"] = TYPE_AUDIO
                complete_object["entry"] = AudioSerializer(
                    audio, context={"request": request, "site": audio.site}
                ).data

            elif (
                ELASTICSEARCH_MEDIA_INDEX in obj["_index"]
                and obj["_source"]["type"] == TYPE_IMAGE
            ):
                image = get_object_by_id(image_objects, obj["_source"]["document_id"])
                complete_object["type"] = TYPE_IMAGE
                complete_object["entry"] = ImageMinimalSerializer(image).data

            elif (
                ELASTICSEARCH_MEDIA_INDEX in obj["_index"]
                and obj["_source"]["type"] == TYPE_VIDEO
            ):
                video = get_object_by_id(video_objects, obj["_source"]["document_id"])
                complete_object["type"] = TYPE_VIDEO
                complete_object["entry"] = VideoMinimalSerializer(video).data
        except Exception as e:
            handle_hydration_errors(obj, e)

        complete_objects.append(complete_object)

    return complete_objects


def handle_hydration_errors(obj, exception):
    """
    Handle exceptions and log errors.
    """
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    document_id = obj["_source"]["document_id"]

    error_message = str(exception)
    log_level = "error"  # default log level

    if "Object not found in db" in error_message:
        # For cases where an indexed object is not present in the database for further hydration
        log_level = "warning"
        log_message = f"Object not found in database with id: {document_id}."
    elif "has no site" in error_message:
        # For cases where an indexed object points to a deleted site
        log_message = f"Missing site object on ES object with id: {document_id}. Error: {error_message}"
    else:
        log_message = f"Error during hydration process. Document id: {document_id}. Error: {error_message}"

    logger.log(logging.getLevelName(log_level.upper()), log_message)
