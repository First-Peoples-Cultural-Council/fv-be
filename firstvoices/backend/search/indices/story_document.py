import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_elasticsearch_dsl import Index
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Keyword, Text

from backend.models.story import Story, StoryPage
from backend.search.indices.base_document import BaseDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_STORY_INDEX,
    ES_CONNECTION_ERROR,
    ES_NOT_FOUND_ERROR,
    SearchIndexEntryTypes,
)
from backend.search.utils.object_utils import get_object_from_index, get_page_info
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
def update_story_index(sender, instance, **kwargs):
    # add story to es index
    try:
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
            ES_CONNECTION_ERROR % ("story", SearchIndexEntryTypes.STORY, instance.id)
        )
        logger.error(e)
    except NotFoundError as e:
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.warning(
            ES_NOT_FOUND_ERROR,
            "get",
            SearchIndexEntryTypes.STORY,
            instance.id,
        )
        logger.warning(e)
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, instance.id)
        logger.error(e)


# Delete entry from index
@receiver(post_delete, sender=Story)
def delete_from_index(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)

    try:
        existing_entry = get_object_from_index(
            ELASTICSEARCH_STORY_INDEX, "story", instance.id
        )
        if existing_entry:
            index_entry = StoryDocument.get(id=existing_entry["_id"])
            index_entry.delete()
    except ConnectionError:
        logger.error(
            ES_CONNECTION_ERROR % ("story", SearchIndexEntryTypes.STORY, instance.id)
        )
    except Exception as e:
        # Fallback exception case
        logger = logging.getLogger(ELASTICSEARCH_LOGGER)
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, instance.id)
        logger.error(e)


# Page update
@receiver(post_delete, sender=StoryPage)
@receiver(post_save, sender=StoryPage)
def update_pages(sender, instance, **kwargs):
    logger = logging.getLogger(ELASTICSEARCH_LOGGER)
    story = instance.story

    page_text, page_translation = get_page_info(story)

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
            % ("story_page", SearchIndexEntryTypes.STORY, instance.id)
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
        logger.error(type(e).__name__, SearchIndexEntryTypes.STORY, instance.id)
        logger.error(e)
