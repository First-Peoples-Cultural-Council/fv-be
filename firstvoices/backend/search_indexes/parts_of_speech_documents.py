from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry

from backend.models.part_of_speech import PartOfSpeech
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG

ELASTICSEARCH_PART_OF_SPEECH_ENTRY_INDEX = "part_of_speech"


@registry.register_document
class DictionaryEntryDocument(Document):
    class Index:
        name = ELASTICSEARCH_PART_OF_SPEECH_ENTRY_INDEX
        settings = ELASTICSEARCH_DEFAULT_CONFIG

    class Django:
        model = PartOfSpeech
        fields = [
            "title",
        ]
