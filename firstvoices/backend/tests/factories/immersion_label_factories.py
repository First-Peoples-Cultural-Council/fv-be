import factory

from backend.models import ImmersionLabel
from backend.tests.factories import DictionaryEntryFactory
from backend.tests.factories.base_factories import BaseSiteContentFactory


class ImmersionLabelFactory(BaseSiteContentFactory):
    class Meta:
        model = ImmersionLabel

    key = factory.Sequence(lambda n: "ImmersionLabel key %03d" % n)
    dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
