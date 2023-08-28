from elasticsearch_dsl import Boolean, Document, Integer, Keyword, Text


class BaseDocument(Document):
    # generic fields, present in all models required to be indexed
    document_id = Keyword()
    site_id = Keyword()
    site_visibility = Integer()
    visibility = Integer()
    exclude_from_games = Boolean()
    exclude_from_kids = Boolean()

    # combined text search fields
    # for boost values for following fields refer search/utils/search_term_query.py
    primary_language_search_fields = Text()
    primary_translation_search_fields = Text()
    secondary_language_search_fields = Text()
    secondary_translation_search_fields = Text()
    other_language_search_fields = Text()
    other_translation_search_fields = Text()
