import factory
from factory.django import DjangoModelFactory

from backend.models.page import SitePage
from backend.tests.factories import SiteFactory


class SitePageFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)
    widgets = factory.SubFactory("backend.tests.factories.SiteWidgetListFactory")

    class Meta:
        model = SitePage

    title = factory.Sequence(lambda n: "SitePage-%03d" % n)
    slug = factory.Sequence(lambda n: "site-page-%03d" % n)
