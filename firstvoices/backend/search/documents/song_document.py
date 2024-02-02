from elasticsearch_dsl import Boolean, Keyword, Text

from backend.search.documents.base_document import (
    BaseSiteEntryDocument,
    MediaReportingDocumentMixin,
)
from backend.search.utils.constants import ELASTICSEARCH_SONG_INDEX


class SongDocument(MediaReportingDocumentMixin, BaseSiteEntryDocument):
    # text search fields
    title = Text(fields={"raw": Keyword()}, copy_to="primary_language_search_fields")
    title_translation = Text(copy_to="primary_translation_search_fields")
    intro_title = Text(copy_to="secondary_language_search_fields")
    intro_translation = Text(copy_to="secondary_translation_search_fields")
    lyrics_text = Text(copy_to="secondary_language_search_fields")
    lyrics_translation = Text(copy_to="secondary_translation_search_fields")
    note = Text(copy_to="other_translation_search_fields")
    acknowledgement = Text(copy_to="other_translation_search_fields")

    # filter and sorting
    has_translation = Boolean()

    class Index:
        name = ELASTICSEARCH_SONG_INDEX
