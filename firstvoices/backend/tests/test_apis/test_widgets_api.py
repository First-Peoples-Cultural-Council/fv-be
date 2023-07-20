import json

import pytest

from backend.models.constants import Visibility
from backend.models.widget import SiteWidget, WidgetSettings
from backend.tests import factories
from backend.tests.test_apis.base_api_test import BaseControlledSiteContentApiTest


class TestSiteWidgetEndpoint(BaseControlledSiteContentApiTest):
    API_LIST_VIEW = "api:sitewidget-list"
    API_DETAIL_VIEW = "api:sitewidget-detail"

    model = SiteWidget

    def create_minimal_instance(self, site, visibility):
        return factories.SiteWidgetFactory.create(site=site, visibility=visibility)

    def get_valid_data(self, site=None):
        settings = []
        for _unused in range(3):
            settings.append(factories.WidgetSettingsFactory.create())

        return {
            "title": "Title",
            "type": "WIDGET_TEXT",
            "format": "Default",
            "settings": list(map(lambda x: {"key": x.key, "value": x.value}, settings)),
        }

    def assert_updated_instance(self, expected_data, actual_instance: SiteWidget):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.widget_type == expected_data["type"]
        assert actual_instance.get_format_display() == expected_data["format"]

        actual_settings = WidgetSettings.objects.filter(widget__id=actual_instance.id)

        assert len(actual_settings) == len(expected_data["settings"])

        for index, setting in enumerate(expected_data["settings"]):
            assert setting["key"] == actual_settings[index].key
            assert setting["value"] == actual_settings[index].value

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]

    def get_expected_list_response_item(self, widget, site):
        return self.get_expected_response(widget, site)

    def get_expected_response(self, widget, site):
        return {
            "id": str(widget.id),
            "title": widget.title,
            "url": f"http://testserver{self.get_detail_endpoint(key=widget.id, site_slug=site.slug)}",
            "visibility": "Public",
            "type": widget.widget_type,
            "format": "Default",
            "settings": [],
        }

    @pytest.mark.django_db
    def test_widget_permissions(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        factories.SiteWidgetFactory.create(site=site, visibility=Visibility.PUBLIC)
        factories.SiteWidgetFactory.create(site=site, visibility=Visibility.MEMBERS)
        factories.SiteWidgetFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["count"] == 1, "did not filter out blocked sites"
        assert len(response_data["results"]) == 1, "did not include available site"

    @pytest.mark.django_db
    def test_detail_widget_settings(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        widget = factories.SiteWidgetFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        settings_one = factories.WidgetSettingsFactory.create(widget=widget)
        settings_two = factories.WidgetSettingsFactory.create(widget=widget)

        response = self.client.get(
            self.get_detail_endpoint(key=widget.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(widget.id)

        assert response_data["settings"] == [
            {
                "key": settings_one.key,
                "value": settings_one.value,
            },
            {
                "key": settings_two.key,
                "value": settings_two.value,
            },
        ]
