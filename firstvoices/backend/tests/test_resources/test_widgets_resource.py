import uuid

import pytest
import tablib

from backend.models.utils import WIDGET_TEXT
from backend.models.widget import SiteWidget, WidgetSettings
from backend.resources.widgets import SiteWidgetResource, WidgetSettingsResource
from backend.tests.factories import SiteFactory, SiteWidgetFactory


class TestSiteWidgetImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,title,visibility,widget_type,format,site",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import SiteWidget object with basic fields"""
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"Sample Widget,Team,{WIDGET_TEXT},Right,{site.id}",
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,"
            f"Widget Title,Public,{WIDGET_TEXT},Default,{site.id}",
        ]
        table = self.build_table(data)

        result = SiteWidgetResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert SiteWidget.objects.filter(site=site.id).count() == len(data)

        new_widget = SiteWidget.objects.get(id=table["id"][0])
        assert table["title"][0] == new_widget.title
        assert table["visibility"][0] == new_widget.get_visibility_display()
        assert table["widget_type"][0] == new_widget.widget_type
        assert table["format"][0] == new_widget.get_format_display()
        assert table["site"][0] == str(new_widget.site.id)

        new_widget = SiteWidget.objects.get(id=table["id"][1])
        assert table["title"][1] == new_widget.title
        assert table["visibility"][1] == new_widget.get_visibility_display()
        assert table["widget_type"][1] == new_widget.widget_type
        assert table["format"][1] == new_widget.get_format_display()
        assert table["site"][1] == str(new_widget.site.id)


class TestWidgetSettingsImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "widget_id,created,created_by,last_modified,last_modified_by,key,value,site",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import WidgetSettings object with basic fields"""
        site = SiteFactory.create()
        site_widget = SiteWidgetFactory.create(site=site)
        data = [
            f"{site_widget.id},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"Setting 1 key,Setting 1 value,{site.id}",
            f"{site_widget.id},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,"
            f"Setting 2 key,Setting 2 value,{site.id}",
        ]
        table = self.build_table(data)

        assert WidgetSettings.objects.filter(widget=site_widget).count() == 0

        result = WidgetSettingsResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert WidgetSettings.objects.filter(widget=site_widget).count() == len(data)

        new_widget_settings = site_widget.widgetsettings_set.get(key=table["key"][0])
        assert table["key"][0] == new_widget_settings.key
        assert table["value"][0] == new_widget_settings.value
        assert new_widget_settings.widget == site_widget

        new_widget = site_widget.widgetsettings_set.get(key=table["key"][1])
        assert table["key"][1] == new_widget.key
        assert table["value"][1] == new_widget.value
        assert new_widget_settings.widget == site_widget
