import factory
from factory.django import DjangoModelFactory

from backend.models import DictionaryEntry, PartOfSpeech
from backend.tests.factories import RelatedMediaBaseFactory, UserFactory
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


