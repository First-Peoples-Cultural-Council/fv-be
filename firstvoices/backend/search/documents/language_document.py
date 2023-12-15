from elasticsearch_dsl import Document, Keyword, Text

from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX


class LanguageDocument(Document):
    primary_search_fields = Text()  # canonical names and identifiers
    secondary_search_fields = Text()  # alternate names and keywords

    language_code = Keyword()  # no fuzzy matching on the language_code
    language_name = Text(fields={"raw": Keyword()}, copy_to="primary_search_fields")
    language_alternate_names = Text(
        fields={"raw": Keyword()}, copy_to="secondary_search_fields"
    )
    language_community_keywords = Text(
        fields={"raw": Keyword()}, copy_to="secondary_search_fields"
    )

    # site_names
    site_names = Text(fields={"raw": Keyword()}, copy_to="primary_search_fields")
    site_slugs = Text(fields={"raw": Keyword()}, copy_to="secondary_search_fields")

    language_family_name = Text(
        fields={"raw": Keyword()}, copy_to="primary_search_fields"
    )
    language_family_alternate_names = Text(
        fields={"raw": Keyword()}, copy_to="secondary_search_fields"
    )

    class Index:
        name = ELASTICSEARCH_LANGUAGE_INDEX