import logging

from celery import shared_task
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Index

from backend.models.story import Story, StoryPage
from backend.search.documents import StoryDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_STORY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_object_from_index, get_page_info
from firstvoices.settings import ELASTICSEARCH_LOGGER


@shared_task(bind=True)
def update_story_index(self, instance_id, **kwargs):
    # add story to es index
    try:
        instance = Story.objects.get(id=instance_id)
        existing_entry = get_object_from_index(
            ELASTICSEARCH_STORY_INDEX, "song", instance.id
        )
        page_text, page_translation = get_page_info(instance)

        if existing_entry:
            index_entry = StoryDocument.get(id=existing_entry["_id"])
            index_entry.update(
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=instance.visibility,
                title=instance.title,
                title_translation=instance.title_translation,
                note=instance.notes,
                acknowledgement=instance.acknowledgements,
                introduction=instance.introduction,
                introduction_translation=instance.introduction_translation,
                author=instance.author,
                page_text=page_text,
                page_translation=page_translation,
            )
        else:
            index_entry = StoryDocument(
                document_id=str(instance.id),
                site_id=str(instance.site.id),
                site_visibility=instance.site.visibility,
                exclude_from_games=instance.exclude_from_games,
                exclude_from_kids=instance.exclude_from_kids,
                visibility=instance.visibility,
                title=instance.title,
                title_translation=instance.title_translation,
                note=instance.notes,
                acknowledgement=instance.acknowledgements,
                introduction=instance.introduction,
                introduction_translation=instance.introduction_translation,
                author=instance.author,
                page_text=page_text,
                page_translation=page_translation,
            )
            index_entry.save()
        # Refresh the index to ensure the index is up-to-date for related field signals
        story_index = Index(ELASTICSEARCH_STORY_INDEX)
        story_index.refresh()
    except ConnectionError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(
            ES_CONNECTION_ERROR % ("story", SearchIndexEntryTypes.STORY, instance_id)
        )
        logger.error(e)
    except NotFoundError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.STORY,
            instance_id,
        )
        logger.warning(e)
    except Story.DoesNotExist as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.DICTIONARY_ENTRY,
            instance_id,
        )
        logger.warning(e)
        self.retry(countdown=5, max_retries=3)
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, instance_id)
        logger.error(e)


@shared_task
def delete_from_index(instance_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_STORY_INDEX, "story", instance_id
        )
        if existing_entry:
            index_entry = StoryDocument.get(id=existing_entry["_id"])
            index_entry.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR % ("story", SearchIndexEntryTypes.STORY, instance_id)
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, instance_id)
        logger.error(e)


@shared_task(bind=True)
def update_pages(self, instance_id, story_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        instance = StoryPage.objects.get(id=instance_id)
        story = Story.objects.get(id=instance.story_id)
        page_text, page_translation = get_page_info(story)

        existing_entry = get_object_from_index(
            ELASTICSEARCH_STORY_INDEX, "story", story.id
        )
        if not existing_entry:
            raise NotFoundError

        story_doc = StoryDocument.get(id=existing_entry["_id"])
        story_doc.update(page_text=page_text, page_translation=page_translation)
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR
            % ("story_page", SearchIndexEntryTypes.STORY, instance_id)
        )
    except NotFoundError:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "story_page_update_signal",
                SearchIndexEntryTypes.STORY,
                story_id,
            )
        )
    except StoryPage.DoesNotExist as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.DICTIONARY_ENTRY,
            instance_id,
        )
        logger.warning(e)
        self.retry(countdown=5, max_retries=3)
    except Story.DoesNotExist:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "pagess_update_signal",
                SearchIndexEntryTypes.STORY,
                story_id,
            )
        )
        return
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, instance_id)
        logger.error(e)
