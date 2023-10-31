import logging

from celery import shared_task
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Index

from backend.models.constants import Visibility
from backend.models.media import Audio, Image, Video
from backend.search.documents import MediaDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_MEDIA_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    RETRY_ON_CONFLICT,
    TYPE_AUDIO,
    TYPE_IMAGE,
    TYPE_VIDEO,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_object_from_index
from firstvoices.settings import ELASTICSEARCH_LOGGER


@shared_task
def update_media_index(instance_id, media_type, **kwargs):
    # get object instance
    media_model_map = {
        TYPE_AUDIO: Audio,
        TYPE_IMAGE: Image,
        TYPE_VIDEO: Video,
    }
    model_class = media_model_map[media_type]
    instance = model_class.objects.get(id=instance_id)

    # Add media to ES index
    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_MEDIA_INDEX, "media", instance.id
        )
        if existing_entry:
            # Check if object is already indexed, then update
            index_entry = MediaDocument.get(id=existing_entry["_id"])
            index_entry.update(
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=Visibility.PUBLIC,
                title=instance.title,
                type=media_type,
                filename=instance.original.content.name,
                description=instance.description,
                retry_on_conflict=RETRY_ON_CONFLICT,
            )
        else:
            index_entry = MediaDocument(
                document_id=str(instance.id),
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=Visibility.PUBLIC,
                title=instance.title,
                type=media_type,
                filename=instance.original.content.name,
                description=instance.description,
            )
            index_entry.save()
        # Refresh the index to ensure the index is up-to-date for related field signals
        media_index = Index(ELASTICSEARCH_MEDIA_INDEX)
        media_index.refresh()
    except ConnectionError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            ES_CONNECTION_ERROR % ("media", SearchIndexEntryTypes.MEDIA, instance_id)
        )
        logger.error(e)
    except NotFoundError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.MEDIA,
            instance_id,
        )
        logger.warning(e)
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.MEDIA, instance_id)
        logger.error(e)


@shared_task
def delete_from_index(instance_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_MEDIA_INDEX, "media", instance_id
        )
        if existing_entry:
            index_entry = MediaDocument.get(id=existing_entry["_id"])
            index_entry.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR % ("media", SearchIndexEntryTypes.MEDIA, instance_id)
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.MEDIA, instance_id)
        logger.error(e)
