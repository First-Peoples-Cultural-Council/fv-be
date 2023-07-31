import json

import pytest

from backend.models.constants import AppRole, Visibility
from backend.models.widget import SiteWidget, WidgetSettings
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseControlledLanguageAdminOnlySiteContentAPITest,
)


class TestSiteWidgetEndpoint(BaseControlledLanguageAdminOnlySiteContentAPITest):
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
            "visibility": "Public",
            "type": "WIDGET_TEXT",
            "format": "Default",
            "settings": list(map(lambda x: {"key": x.key, "value": x.value}, settings)),
        }

    def add_related_objects(self, instance):
        factories.WidgetSettingsFactory.create(widget=instance)
        factories.WidgetSettingsFactory.create(widget=instance)

    def assert_related_objects_deleted(self, instance):
        for setting in instance.widgetsettings_set.all():
            self.assert_instance_deleted(setting)

    def assert_updated_instance(self, expected_data, actual_instance: SiteWidget):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.widget_type == expected_data["type"]
        assert actual_instance.get_visibility_display() == expected_data["visibility"]
        assert actual_instance.get_format_display() == expected_data["format"]

        actual_settings = WidgetSettings.objects.filter(widget__id=actual_instance.id)

        assert len(actual_settings) == len(expected_data["settings"])

        for index, setting in enumerate(expected_data["settings"]):
            assert setting["key"] == actual_settings[index].key
            assert setting["value"] == actual_settings[index].value

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        return self.get_expected_response(instance, instance.site)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

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

        assert {
            "key": settings_one.key,
            "value": settings_one.value,
        } in response_data["settings"]
        assert {
            "key": settings_two.key,
            "value": settings_two.value,
        } in response_data["settings"]

    @pytest.mark.django_db
    def test_detail_widget_create(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        data = {
            "title": "Title",
            "visibility": "Public",
            "type": "WIDGET_TEXT",
            "format": "Default",
            "settings": [
                {"key": "key: 000", "value": "value: 000"},
            ],
        }

        assert len(SiteWidget.objects.all()) == 0
        assert len(WidgetSettings.objects.all()) == 0

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        assert len(SiteWidget.objects.all()) == 1
        assert len(WidgetSettings.objects.all()) == 1

        widget = SiteWidget.objects.all().first()
        settings = WidgetSettings.objects.all().first()

        assert widget.title == data["title"]
        assert widget.get_visibility_display() == data["visibility"]
        assert widget.widget_type == data["type"]
        assert widget.get_format_display() == data["format"]
        assert settings.key == data["settings"][0]["key"]
        assert settings.value == data["settings"][0]["value"]

    @pytest.mark.django_db
    def test_detail_widget_create_no_settings(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        data = {
            "title": "Title",
            "visibility": "Public",
            "type": "WIDGET_TEXT",
            "format": "Default",
            "settings": [],
        }

        assert len(SiteWidget.objects.all()) == 0
        assert len(WidgetSettings.objects.all()) == 0

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        assert len(SiteWidget.objects.all()) == 1
        assert len(WidgetSettings.objects.all()) == 0

        widget = SiteWidget.objects.all().first()

        assert widget.title == data["title"]
        assert widget.get_visibility_display() == data["visibility"]
        assert widget.widget_type == data["type"]
        assert widget.get_format_display() == data["format"]

    @pytest.mark.django_db
    def test_detail_widget_settings_update(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        widget = SiteWidget.objects.create(site=site)

        data = {
            "title": "Title Updated",
            "visibility": "Public",
            "type": "WIDGET_TEXT",
            "format": "Default",
            "settings": [
                {"key": "key: 000", "value": "value: 000"},
            ],
        }

        assert len(SiteWidget.objects.all()) == 1
        assert len(WidgetSettings.objects.all()) == 0

        response = self.client.put(
            self.get_detail_endpoint(key=widget.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        assert len(SiteWidget.objects.all()) == 1
        assert len(WidgetSettings.objects.all()) == 1

        widget = SiteWidget.objects.all().first()
        settings = WidgetSettings.objects.all().first()

        assert widget.title == data["title"]
        assert widget.get_visibility_display() == data["visibility"]
        assert widget.widget_type == data["type"]
        assert widget.get_format_display() == data["format"]
        assert settings.key == data["settings"][0]["key"]
        assert settings.value == data["settings"][0]["value"]

        data_no_settings = {
            "title": "Title Updated Two",
            "visibility": "Public",
            "type": "WIDGET_TEXT",
            "format": "Default",
            "settings": [],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=widget.id, site_slug=site.slug),
            format="json",
            data=data_no_settings,
        )
        assert response.status_code == 200

        assert len(SiteWidget.objects.all()) == 1
        assert len(WidgetSettings.objects.all()) == 0

        widget = SiteWidget.objects.all().first()

        assert widget.title == data_no_settings["title"]
        assert widget.get_visibility_display() == data_no_settings["visibility"]
        assert widget.widget_type == data_no_settings["type"]
        assert widget.get_format_display() == data_no_settings["format"]

    @pytest.mark.django_db
    def test_detail_widget_delete(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        widget = factories.SiteWidgetFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        settings_one = factories.WidgetSettingsFactory.create(widget=widget)

        assert SiteWidget.objects.filter(id=widget.id).exists()
        assert WidgetSettings.objects.filter(id=settings_one.id).exists()
        assert len(SiteWidget.objects.all()) == 1
        assert len(WidgetSettings.objects.all()) == 1

        response = self.client.delete(
            self.get_detail_endpoint(key=widget.id, site_slug=site.slug)
        )

        assert response.status_code == 204
        assert not SiteWidget.objects.filter(id=widget.id).exists()
        assert not WidgetSettings.objects.filter(id=settings_one.id).exists()
        assert len(SiteWidget.objects.all()) == 0
        assert len(WidgetSettings.objects.all()) == 0
