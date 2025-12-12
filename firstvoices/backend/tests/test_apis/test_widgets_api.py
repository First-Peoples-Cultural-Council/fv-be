import json

import pytest

from backend.models.constants import WIDGET_TEXT, AppRole, Role, Visibility
from backend.models.widget import SiteWidget, WidgetFormats, WidgetSettings
from backend.tests import factories
from backend.tests.test_apis.base.base_controlled_site_api import (
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
            "type": "WIDGET_CUSTOM",
            "format": WidgetFormats.FULL.label,
            "settings": list(map(lambda x: {"key": x.key, "value": x.value}, settings)),
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "Title",
            "visibility": "Public",
            "type": "WIDGET_TESTING",
            "format": WidgetFormats.CENTER.label,
        }

    def add_expected_defaults(self, data):
        return {**data, "settings": []}

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

    def get_expected_response(self, instance, site):
        controlled_standard_fields = self.get_expected_controlled_standard_fields(
            instance, site
        )
        return {
            **controlled_standard_fields,
            "type": instance.widget_type,
            "format": "Default",
            "settings": [],
        }

    def create_original_instance_for_patch(self, site):
        widget = factories.SiteWidgetFactory.create(
            site=site, title="Title", widget_type="Type", format=WidgetFormats.LEFT
        )
        factories.WidgetSettingsFactory.create(widget=widget)

        return widget

    def get_valid_patch_data(self, site=None):
        return {"title": "Title Updated"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: SiteWidget
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.site == original_instance.site
        assert updated_instance.visibility == original_instance.visibility
        assert updated_instance.widget_type == original_instance.widget_type
        assert updated_instance.format == original_instance.format
        assert (
            updated_instance.widgetsettings_set.first()
            == original_instance.widgetsettings_set.first()
        )

    def assert_patch_instance_updated_fields(self, data, updated_instance: SiteWidget):
        assert updated_instance.title == data["title"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["title"] == data["title"]
        assert (
            actual_response["visibility"]
            == original_instance.get_visibility_display().lower()
        )
        assert actual_response["type"] == original_instance.widget_type
        assert actual_response["format"] == original_instance.get_format_display()
        assert (
            actual_response["settings"][0]["key"]
            == original_instance.widgetsettings_set.first().key
        )
        assert (
            actual_response["settings"][0]["value"]
            == original_instance.widgetsettings_set.first().value
        )

    @pytest.mark.django_db
    def test_list_permissions(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        self.create_minimal_instance(site=site, visibility=Visibility.MEMBERS)
        self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == default_widgets_count + 1
        assert len(response_data["results"]) == default_widgets_count + 1

        # getting current widget from list of widgets
        widget = list(
            filter(lambda x: x["id"] == str(instance.id), response_data["results"])
        )[0]

        assert widget == self.get_expected_list_response_item_no_email_access(
            instance, site
        )

    @pytest.mark.skip(
        reason="Test is same as test_list_permissions. Removed the code to reduce duplication."
    )
    def test_list_minimal(self):
        # Skipping test as it is same as the test_list_permissions test above.
        pass

    @pytest.mark.skip(
        reason="Site widget API does not have eligible optional charfields."
    )
    def test_create_with_null_optional_charfields_success_201(self):
        # Site widget API does not have eligible optional charfields.
        pass

    @pytest.mark.skip(
        reason="Site widget API does not have eligible optional charfields."
    )
    def test_update_with_null_optional_charfields_success_200(self):
        # Site widget API does not have eligible optional charfields.
        pass

    @pytest.mark.django_db
    def test_list_empty(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == default_widgets_count

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == default_widgets_count

    @pytest.mark.django_db
    def test_list_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == default_widgets_count

    @pytest.mark.django_db
    def test_widget_permissions(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        factories.SiteWidgetFactory.create(site=site, visibility=Visibility.PUBLIC)
        factories.SiteWidgetFactory.create(site=site, visibility=Visibility.MEMBERS)
        factories.SiteWidgetFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert (
            response_data["count"] == default_widgets_count + 1
        ), "did not filter out blocked sites"
        assert (
            len(response_data["results"]) == default_widgets_count + 1
        ), "did not include available site"

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
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        data = {
            "title": "Title",
            "visibility": "Public",
            "type": WIDGET_TEXT,
            "format": "Default",
            "settings": [
                {"key": "key: 000", "value": "value: 000"},
            ],
        }

        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count
        assert len(WidgetSettings.objects.all()) == 0

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 1
        assert len(WidgetSettings.objects.all()) == 1

        widget = SiteWidget.objects.filter(title=data["title"]).first()
        settings = WidgetSettings.objects.filter(widget=widget).first()

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
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        data = {
            "title": "Title",
            "visibility": "Public",
            "type": WIDGET_TEXT,
            "format": "Default",
            "settings": [],
        }

        assert len(SiteWidget.objects.all()) == default_widgets_count
        assert len(WidgetSettings.objects.all()) == 0

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 1
        assert len(WidgetSettings.objects.all()) == 0

        widget = SiteWidget.objects.filter(title=data["title"]).first()

        assert widget.get_visibility_display() == data["visibility"]
        assert widget.widget_type == data["type"]
        assert widget.get_format_display() == data["format"]

    @pytest.mark.django_db
    def test_detail_widget_settings_update(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        widget = SiteWidget.objects.create(site=site)

        data = {
            "title": "Title Updated",
            "visibility": "Public",
            "type": WIDGET_TEXT,
            "format": "Default",
            "settings": [
                {"key": "key: 000", "value": "value: 000"},
            ],
        }

        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 1
        assert len(WidgetSettings.objects.all()) == 0

        response = self.client.put(
            self.get_detail_endpoint(key=widget.id, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 1
        assert len(WidgetSettings.objects.all()) == 1

        widget = SiteWidget.objects.filter(title=data["title"]).first()
        settings = WidgetSettings.objects.filter(widget=widget).first()

        assert widget.get_visibility_display() == data["visibility"]
        assert widget.widget_type == data["type"]
        assert widget.get_format_display() == data["format"]
        assert settings.key == data["settings"][0]["key"]
        assert settings.value == data["settings"][0]["value"]

        data_no_settings = {
            "title": "Title Updated Two",
            "visibility": "Public",
            "type": WIDGET_TEXT,
            "format": "Default",
            "settings": [],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=widget.id, site_slug=site.slug),
            format="json",
            data=data_no_settings,
        )
        assert response.status_code == 200

        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 1
        assert len(WidgetSettings.objects.all()) == 0

        widget = SiteWidget.objects.filter(title=data_no_settings["title"]).first()

        assert widget.get_visibility_display() == data_no_settings["visibility"]
        assert widget.widget_type == data_no_settings["type"]
        assert widget.get_format_display() == data_no_settings["format"]

    @pytest.mark.django_db
    def test_detail_widget_delete(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()
        self.client.force_authenticate(user=user)

        widget = factories.SiteWidgetFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        settings_one = factories.WidgetSettingsFactory.create(widget=widget)

        assert SiteWidget.objects.filter(id=widget.id).exists()
        assert WidgetSettings.objects.filter(id=settings_one.id).exists()
        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 1
        assert len(WidgetSettings.objects.all()) == 1

        response = self.client.delete(
            self.get_detail_endpoint(key=widget.id, site_slug=site.slug)
        )

        assert response.status_code == 204
        assert not SiteWidget.objects.filter(id=widget.id).exists()
        assert not WidgetSettings.objects.filter(id=settings_one.id).exists()
        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count
        assert len(WidgetSettings.objects.all()) == 0
