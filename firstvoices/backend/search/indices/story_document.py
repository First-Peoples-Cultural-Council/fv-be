import logging

from celery import shared_task
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Index, Keyword, Text

from backend.models.story import Story, StoryPage
from backend.search.indices.base_document import BaseDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_STORY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_object_from_index, get_page_info
from firstvoices.celery import link_error_handler
from firstvoices.settings import ELASTICSEARCH_LOGGER


class StoryDocument(BaseDocument):
    # text search fields
    title = Text(fields={"raw": Keyword()}, copy_to="primary_language_search_fields")
    title_translation = Text(copy_to="primary_translation_search_fields")
    introduction = Text(copy_to="secondary_language_search_fields")
    introduction_translation = Text(copy_to="secondary_translation_search_fields")
    page_text = Text(copy_to="secondary_language_search_fields")
    page_translation = Text(copy_to="secondary_translation_search_fields")
    acknowledgement = Text(copy_to="other_translation_search_fields")
    note = Text(copy_to="other_translation_search_fields")
    author = Text(copy_to="other_translation_search_fields")

    # Author to be added

    class Index:
        name = ELASTICSEARCH_STORY_INDEX


@receiver(post_save, sender=Story)
def request_update_story_index(sender, instance, **kwargs):
    if Story.objects.filter(id=instance.id).exists():
        update_story_index.apply_async(
            (instance.id,), countdown=2, link_error=link_error_handler.s()
        )


@shared_task
def update_story_index(instance_id, **kwargs):
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
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, instance_id)
        logger.error(e)


# Delete entry from index
@receiver(post_delete, sender=Story)
def request_delete_from_index(sender, instance, **kwargs):
    delete_from_index.apply_async((instance.id,), link_error=link_error_handler.s())


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


# Page update
@receiver(post_delete, sender=StoryPage)
@receiver(post_save, sender=StoryPage)
def request_update_pages(sender, instance, **kwargs):
    update_pages.apply_async(
        (instance.id, instance.story.id), countdown=2, link_error=link_error_handler.s()
    )


@shared_task
def update_pages(instance_id, story_id, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    # Set story and page text. If it doesn't exist due to deletion, warn and return.
    try:
        story = Story.objects.get(id=story_id)
        page_text, page_translation = get_page_info(story)
    except Story.DoesNotExist:
        logger.warning(
            ES_NOT_FOUND_ERROR
            % (
                "story_page_update_signal",
                SearchIndexEntryTypes.STORY,
                story_id,
            )
        )
        return

    try:
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
                story.id,
            )
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, instance_id)
        logger.error(e)
