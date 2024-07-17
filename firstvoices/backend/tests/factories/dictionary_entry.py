import factory
from factory.django import DjangoModelFactory

from backend.models import DictionaryEntry, PartOfSpeech
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.access import SiteFactory, UserFactory


class PartOfSpeechFactory(DjangoModelFactory):
    class Meta:
        model = PartOfSpeech

    title = factory.Sequence(lambda n: "Part of Speech %03d" % n)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)


class DictionaryEntryFactory(RelatedMediaBaseFactory):
    class Meta:
        model = DictionaryEntry

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)
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
