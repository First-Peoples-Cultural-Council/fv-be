import pytest
import tablib

from backend.models import Site
from backend.models.widget import SiteWidget, SiteWidgetList, SiteWidgetListOrder
from backend.resources.site_homepage_widgets import SiteHomepageWidgetsResource
from backend.tests import factories


class TestSiteHomepageWidgetsImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,title,slug,visibility,language,contact_email,"
            "homepage_widgets",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        site = factories.SiteFactory.create()
        user1 = factories.UserFactory.create()
        user2 = factories.UserFactory.create()
        widget1 = factories.SiteWidgetFactory.create(site=site)
        widget2 = factories.SiteWidgetFactory.create(site=site)

        data = [
            f"{str(site.id)},2023-02-02 21:21:10.713,{user1.email},2023-02-02 21:21:39.864,{user2.email},Sample site "
            f'title,sample-site-slug,Public,,test@email.com,"{str(widget1.id)},{str(widget2.id)}"',
        ]
        table = self.build_table(data)

        assert site.homepage is None
        assert len(SiteWidget.objects.all()) == 2
        assert len(SiteWidgetList.objects.all()) == 0
        assert len(SiteWidgetListOrder.objects.all()) == 0

        result = SiteHomepageWidgetsResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["update"] == len(data)
        site = Site.objects.get(id=table["id"][0])
        assert site.homepage is not None

        assert (
            SiteWidgetListOrder.objects.get(
                site_widget_list=site.homepage, order=0
            ).site_widget
            == widget1
        )
        assert (
            SiteWidgetListOrder.objects.get(
                site_widget_list=site.homepage, order=1
            ).site_widget
            == widget2
        )

        assert site.homepage.widgets.count() == 2
        assert len(SiteWidget.objects.all()) == 2
        assert len(SiteWidgetList.objects.all()) == 1
        assert len(SiteWidgetListOrder.objects.all()) == 2
