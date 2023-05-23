from elasticsearch_dsl import Document, Text, connections

from firstvoices.settings import ELASTICSEARCH_HOST

ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entry"

# Establish connection
connections.configure(default={"hosts": ELASTICSEARCH_HOST})


class DictionaryEntryDocument(Document):
    # Add details in the following fields for further optimisation
    _id = Text()
    title = Text()
    type = Text()

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX


def save_to_index(_id, title, doc_type):
    index_entry = DictionaryEntryDocument(_id=_id, title=title, type=doc_type)
    index_entry.save()
