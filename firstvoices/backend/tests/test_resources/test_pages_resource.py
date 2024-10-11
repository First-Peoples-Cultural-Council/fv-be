import uuid

import pytest
import tablib

from backend.models import SitePage
from backend.models.widget import SiteWidget, SiteWidgetList, SiteWidgetListOrder
from backend.resources.pages import SitePageResource
from backend.tests import factories
from backend.tests.factories import SiteFactory


@pytest.mark.skip("Tests are for initial migration only")
class TestSitePageImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,title,subtitle,visibility,slug,banner_image,"
            "banner_video,site,widgets",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import SitePage object with basic fields"""
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f'Sample Page,Sample Page Subtitle,Team,sample-page,{uuid.uuid4()},,{site.id},"{str(uuid.uuid4())}"',
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,"
            f"Sample Page Two,Sample Page Subtitle Two,Public,sample-page-two,,{uuid.uuid4()},{site.id},"
            f'"{str(uuid.uuid4())},{str(uuid.uuid4())}"',
        ]
        table = self.build_table(data)

        factories.ImageFactory.create(id=table["banner_image"][0], site=site)
        factories.VideoFactory.create(id=table["banner_video"][1], site=site)
        factories.SiteWidgetFactory.create(
            id=table["widgets"][0].split(",")[0], site=site
        )
        factories.SiteWidgetFactory.create(
            id=table["widgets"][1].split(",")[0], site=site
        )
        factories.SiteWidgetFactory.create(
            id=table["widgets"][1].split(",")[1], site=site
        )

        assert len(SitePage.objects.all()) == 0
        assert len(SiteWidget.objects.all()) == 3
        assert len(SiteWidgetList.objects.all()) == 0
        assert len(SiteWidgetListOrder.objects.all()) == 0

        result = SitePageResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert SitePage.objects.filter(site=site.id).count() == len(data)

        new_page = SitePage.objects.get(id=table["id"][0])
        assert new_page.title == table["title"][0]
        assert new_page.subtitle == table["subtitle"][0]
        assert new_page.get_visibility_display() == table["visibility"][0]
        assert new_page.slug == table["slug"][0]
        assert str(new_page.banner_image.id) == table["banner_image"][0]
        assert new_page.banner_video is None
        assert str(new_page.site.id) == table["site"][0]
        assert new_page.widgets
        assert len(new_page.widgets.widgets.all()) == 1

        new_page = SitePage.objects.get(id=table["id"][1])
        assert new_page.title == table["title"][1]
        assert new_page.subtitle == table["subtitle"][1]
        assert new_page.get_visibility_display() == table["visibility"][1]
        assert new_page.slug == table["slug"][1]
        assert new_page.banner_image is None
        assert str(new_page.banner_video.id) == table["banner_video"][1]
        assert str(new_page.site.id) == table["site"][1]
        assert new_page.widgets
        assert len(new_page.widgets.widgets.all()) == 2

        assert len(SitePage.objects.all()) == 2
        assert len(SiteWidget.objects.all()) == 3
        assert len(SiteWidgetList.objects.all()) == 2
        assert len(SiteWidgetListOrder.objects.all()) == 3
