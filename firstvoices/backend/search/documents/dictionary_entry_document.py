from elasticsearch_dsl import Boolean, Keyword, Text
from elasticsearch_dsl.analysis import analyzer
from elasticsearch_dsl.field import TokenCount

from backend.search.documents.base_document import BaseSiteEntryWithMediaDocument
from backend.search.utils.constants import ELASTICSEARCH_DICTIONARY_ENTRY_INDEX


class DictionaryEntryDocument(BaseSiteEntryWithMediaDocument):
    # text search fields
    title = Text(
        fields={
            "raw": Keyword(),
            "token_count": TokenCount(analyzer=analyzer("standard")),
        },
        copy_to="primary_language_search_fields",
    )
    translation = Text(copy_to="primary_translation_search_fields")
    note = Text(copy_to="other_translation_search_fields")
    acknowledgement = Text(copy_to="other_translation_search_fields")
    alternate_spelling = Text(copy_to="primary_language_search_fields")

    # filter and sorting
    type = Keyword()
    custom_order = Keyword()
    categories = Keyword()
    import_job_id = Keyword()
    has_translation = Boolean()
    has_unrecognized_chars = Boolean()
    has_categories = Boolean()
    has_related_entries = Boolean()

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
