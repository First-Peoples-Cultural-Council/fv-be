import factory

from backend.models import DictionaryEntry
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.access import SiteFactory


class DictionaryEntryFactory(RelatedMediaBaseFactory):
    class Meta:
        model = DictionaryEntry

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Dictionary entry %03d" % n)
    custom_order = factory.Sequence(lambda n: "sort order %03d" % n)
