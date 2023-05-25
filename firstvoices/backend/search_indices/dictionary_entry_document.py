from elasticsearch_dsl import Document, Index, Keyword, Text

from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG

ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entry"

# Defining index and settings
dictionary_entries = Index(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX)
dictionary_entries.settings(
    number_of_shards=ELASTICSEARCH_DEFAULT_CONFIG["shards"],
    number_of_replicas=ELASTICSEARCH_DEFAULT_CONFIG["replicas"],
)


@dictionary_entries.document
class DictionaryEntryDocument(Document):
    _id = Text()
    title = Text()
    type = Keyword()

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
