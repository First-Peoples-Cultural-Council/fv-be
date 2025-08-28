from elasticsearch.dsl import Boolean, Keyword, Text

from backend.search.constants import ELASTICSEARCH_STORY_INDEX
from backend.search.documents.base_document import BaseSiteEntryWithMediaDocument


class StoryDocument(BaseSiteEntryWithMediaDocument):
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

    # filter and sorting
    has_translation = Boolean()

    class Index:
        name = ELASTICSEARCH_STORY_INDEX
