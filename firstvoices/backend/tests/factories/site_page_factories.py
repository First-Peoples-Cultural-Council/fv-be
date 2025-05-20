import factory

from backend.models.page import SitePage
from backend.tests.factories.base_factories import SiteContentFactory


class SitePageFactory(SiteContentFactory):
    class Meta:
        model = SitePage

    widgets = factory.SubFactory("backend.tests.factories.SiteWidgetListFactory")
    title = factory.Sequence(lambda n: "SitePage-%03d" % n)
    slug = factory.Sequence(lambda n: "site-page-%03d" % n)
