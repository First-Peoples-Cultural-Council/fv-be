from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from backend.models.dictionary import DictionaryEntry, Translation
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG

ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entry"


@registry.register_document
class DictionaryEntryDocument(Document):
    translation_set = fields.NestedField(
        properties={"id": fields.TextField(), "text": fields.TextField()}
    )

    class Index:
        name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
        settings = ELASTICSEARCH_DEFAULT_CONFIG

    class Django:
        model = DictionaryEntry
        fields = [
            "title",
            "type",
        ]
        related_models = [Translation]  # Discuss which models should trigger re-index

    def get_instances_from_related(self, related_instance):
        """
        When a related model mentioned above is updated, we want to update the dictionaryEntry as well.
        Here we specify how to reach dictionaryEntries associated from the related model.
        """

        if isinstance(related_instance, Translation):
            return related_instance.dictionary_entry
