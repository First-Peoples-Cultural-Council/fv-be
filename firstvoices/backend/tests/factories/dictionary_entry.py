import factory

from backend.models import DictionaryEntry, PartOfSpeech
from backend.models.dictionary import ExternalDictionaryEntrySystem
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.base_factories import BaseFactory, BaseSiteContentFactory


class PartOfSpeechFactory(BaseFactory):
    class Meta:
        model = PartOfSpeech

    title = factory.Sequence(lambda n: "Part of Speech %03d" % n)


class DictionaryEntryFactory(BaseSiteContentFactory, RelatedMediaBaseFactory):
    class Meta:
        model = DictionaryEntry

    title = factory.Sequence(lambda n: "Dictionary entry %03d" % n)
    custom_order = factory.Sequence(lambda n: "sort order %03d" % n)
    part_of_speech = factory.SubFactory(PartOfSpeechFactory)

    # ManyToOne models migration fields
    notes = factory.List([factory.Sequence(lambda n: "Note %03d" % n)])
    translations = factory.List([factory.Sequence(lambda n: "Translation %03d" % n)])
    acknowledgements = factory.List(
        [factory.Sequence(lambda n: "Acknowledgement %03d" % n)]
    )
    pronunciations = factory.List(
        [factory.Sequence(lambda n: "Pronunciation %03d" % n)]
    )
    alternate_spellings = factory.List(
        [factory.Sequence(lambda n: "Alternate Spelling %03d" % n)]
    )


class ExternalDictionaryEntrySystemFactory(BaseFactory):
    class Meta:
        model = ExternalDictionaryEntrySystem

    title = factory.Sequence(lambda n: "External dictionary entry system %03d" % n)
