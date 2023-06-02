import factory
from factory.django import DjangoModelFactory

from backend.models.sites import Language, LanguageFamily, SiteFeature, SiteMenu
from backend.tests.factories.access import SiteFactory


class SiteFeatureFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SiteFeature

    key = factory.Sequence(lambda n: "Feature %03d" % n)


class LanguageFamilyFactory(DjangoModelFactory):
    class Meta:
        model = LanguageFamily

    title = factory.Sequence(lambda n: "Language Family %03d" % n)


class LanguageFactory(DjangoModelFactory):
    class Meta:
        model = Language

    title = factory.Sequence(lambda n: "Language %03d" % n)
    language_family = factory.SubFactory(LanguageFamilyFactory)


class SiteMenuFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SiteMenu

    json = factory.Sequence(lambda n: "{'menu_json': %03d }" % n)
