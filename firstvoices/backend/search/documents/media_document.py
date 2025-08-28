from elasticsearch.dsl import Keyword, Text

from backend.search.constants import ELASTICSEARCH_MEDIA_INDEX
from backend.search.documents.base_document import BaseSiteEntryDocument


class MediaDocument(BaseSiteEntryDocument):
    # text search fields
    title = Text(fields={"raw": Keyword()}, copy_to="primary_language_search_fields")
    filename = Text(copy_to="other_translation_search_fields")
    description = Text(copy_to="other_translation_search_fields")

    # filter and sorting
    type = Keyword()  # possible values => audio, image, video
    has_site_feature = Keyword()

    class Index:
        name = ELASTICSEARCH_MEDIA_INDEX
