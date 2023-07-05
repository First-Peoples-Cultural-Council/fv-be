import json

import pytest

from backend.models.constants import Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyControlledSiteContentApiTest,
)


class TestSiteWidgetEndpoint(BaseReadOnlyControlledSiteContentApiTest):
    API_LIST_VIEW = "api:sitewidget-list"
    API_DETAIL_VIEW = "api:sitewidget-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.SiteWidgetFactory.create(site=site, visibility=visibility)

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
