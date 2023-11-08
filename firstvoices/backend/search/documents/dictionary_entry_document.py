from elasticsearch_dsl import Keyword, Text

from backend.search.documents.base_document import (
    BaseDocument,
    MediaReportingDocumentMixin,
)
from backend.search.utils.constants import ELASTICSEARCH_DICTIONARY_ENTRY_INDEX


class DictionaryEntryDocument(MediaReportingDocumentMixin, BaseDocument):
    # text search fields
    title = Text(fields={"raw": Keyword()}, copy_to="primary_language_search_fields")
    translation = Text(copy_to="primary_translation_search_fields")
    note = Text(copy_to="other_translation_search_fields")
    acknowledgement = Text(copy_to="other_translation_search_fields")

    # filter and sorting
    type = Keyword()
    custom_order = Keyword()
    categories = Keyword()

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
