from elasticsearch_dsl import Boolean, Keyword, Text

from backend.search.documents.base_document import (
    BaseSiteEntryDocument,
    MediaReportingDocumentMixin,
)
from backend.search.utils.constants import ELASTICSEARCH_DICTIONARY_ENTRY_INDEX


class DictionaryEntryDocument(MediaReportingDocumentMixin, BaseSiteEntryDocument):
    # text search fields
    title = Text(fields={"raw": Keyword()}, copy_to="primary_language_search_fields")
    translation = Text(copy_to="primary_translation_search_fields")
    note = Text(copy_to="other_translation_search_fields")
    acknowledgement = Text(copy_to="other_translation_search_fields")

    # filter and sorting
    type = Keyword()
    custom_order = Keyword()
    categories = Keyword()
    has_translation = Boolean()
    has_unrecognized_chars = Boolean()

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
