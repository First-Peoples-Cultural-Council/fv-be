import factory
from factory.django import DjangoModelFactory

from backend.models import ImmersionLabel
from backend.tests.factories import DictionaryEntryFactory, SiteFactory, UserFactory


class ImmersionLabelFactory(DjangoModelFactory):
    class Meta:
        model = ImmersionLabel

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)
    key = factory.Sequence(lambda n: "ImmersionLabel key %03d" % n)
    dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
