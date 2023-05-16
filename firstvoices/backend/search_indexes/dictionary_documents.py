from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry

from backend.models.dictionary import DictionaryEntry
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG

ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entry"


@registry.register_document
class DictionaryEntryDocument(Document):
    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
        settings = ELASTICSEARCH_DEFAULT_CONFIG

    class Django:
        model = DictionaryEntry
        fields = [
            "title",
            "type",
        ]
