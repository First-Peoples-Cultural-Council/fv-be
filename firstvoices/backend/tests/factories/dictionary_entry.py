import factory

from backend.models import DictionaryEntry
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.access import SiteFactory, UserFactory


class DictionaryEntryFactory(RelatedMediaBaseFactory):
    class Meta:
        model = DictionaryEntry

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Dictionary entry %03d" % n)
    custom_order = factory.Sequence(lambda n: "sort order %03d" % n)
