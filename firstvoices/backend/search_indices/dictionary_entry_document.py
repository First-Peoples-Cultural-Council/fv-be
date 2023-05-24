from elasticsearch_dsl import Document, Index, Text

ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entry"

# Defining index and settings
dictionary_entries = Index(ELASTICSEARCH_DICTIONARY_ENTRY_INDEX)
dictionary_entries.settings(number_of_shards=1, number_of_replicas=0)


@dictionary_entries.document
class DictionaryEntryDocument(Document):
    _id = Text()
    title = Text()
    type = Text()

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
