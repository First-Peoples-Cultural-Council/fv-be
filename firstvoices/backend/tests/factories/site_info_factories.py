import factory
from factory.django import DjangoModelFactory

from backend.models.sites import SiteFeature, SiteMenu
from backend.tests.factories import SiteFactory, UserFactory


class SiteFeatureFactory(DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SiteFeature

    key = factory.Sequence(lambda n: "Feature %03d" % n)


class SiteMenuFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SiteMenu

    json = factory.Sequence(lambda n: "{'menu_json': %03d }" % n)
