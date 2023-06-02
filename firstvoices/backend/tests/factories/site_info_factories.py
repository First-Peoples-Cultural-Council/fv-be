import factory
from factory.django import DjangoModelFactory

from backend.models.sites import SiteFeature, SiteMenu
from backend.tests.factories.access import SiteFactory


class SiteFeatureFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SiteFeature

    key = factory.Sequence(lambda n: "Feature %03d" % n)


class SiteMenuFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SiteMenu

    json = factory.Sequence(lambda n: "{'menu_json': %03d }" % n)
