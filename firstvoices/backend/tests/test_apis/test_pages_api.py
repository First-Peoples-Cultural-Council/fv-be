import json

import pytest

from backend.models.constants import Role, Visibility
from backend.models.widget import SiteWidgetListOrder
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyControlledSiteContentApiTest,
)
from backend.tests.utils import setup_widget_list, update_widget_list_order


class TestSitePageEndpoint(BaseReadOnlyControlledSiteContentApiTest):
    API_LIST_VIEW = "api:sitepage-list"
    API_DETAIL_VIEW = "api:sitepage-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.SitePageFactory.create(site=site, visibility=visibility)

    def get_expected_response(self, page, site):
        return {
            "id": str(page.id),
            "title": page.title,
            "url": f"http://testserver{self.get_detail_endpoint(key=page.slug, site_slug=site.slug)}",
            "visibility": "Public",
            "subtitle": "",
            "slug": page.slug,
        }

    def get_expected_detail_response(self, page, site):
        return {
            "id": str(page.id),
            "title": page.title,
            "url": f"http://testserver{self.get_detail_endpoint(key=page.slug, site_slug=site.slug)}",
            "visibility": "Public",
            "subtitle": "",
            "slug": page.slug,
            "widgets": [],
            "bannerImage": None,
            "bannerVideo": None,
        }

    @pytest.mark.parametrize(
        "user_role, expected_visible_pages",
        [
            (None, 1),
            (Role.MEMBER, 2),
            (Role.ASSISTANT, 3),
            (Role.EDITOR, 3),
            (Role.LANGUAGE_ADMIN, 3),
        ],
    )
    @pytest.mark.django_db
    def test_page_permissions(self, user_role, expected_visible_pages):
        user = factories.UserFactory.create(id=1)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        if user_role is not None:
            factories.MembershipFactory.create(user=user, site=site, role=user_role)

        factories.SitePageFactory.create(site=site, visibility=Visibility.PUBLIC)
        factories.SitePageFactory.create(site=site, visibility=Visibility.MEMBERS)
        factories.SitePageFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(f"{self.get_list_endpoint(site.slug)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["results"]) == expected_visible_pages

    def update_widget_sites(self, site, widgets):
        for widget in widgets:
            widget.site = site
            widget.save()

    @pytest.mark.django_db
    def test_detail_widget_order(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.SiteWidgetListOrderFactory.reset_sequence()
        widget_list = factories.SiteWidgetListWithThreeWidgetsFactory.create(site=site)

        # Get the widgets from the widget list
        widget_one = widget_list.widgets.all()[0]
        widget_two = widget_list.widgets.all()[1]
        widget_three = widget_list.widgets.all()[2]
        self.update_widget_sites(site, [widget_one, widget_two, widget_three])

        site_page = factories.SitePageFactory.create(
            site=site, visibility=Visibility.PUBLIC, widgets=widget_list
        )

        # Get the order field for each widget from the through model
        list_order_one = (
            SiteWidgetListOrder.objects.filter(site_widget=widget_one).first().order
        )
        list_order_two = (
            SiteWidgetListOrder.objects.filter(site_widget=widget_two).first().order
        )
        list_order_three = (
            SiteWidgetListOrder.objects.filter(site_widget=widget_three).first().order
        )

        # Check the order of the widgets as they were created.
        assert list_order_one == 2
        assert list_order_two == 0
        assert list_order_three == 1

        response = self.client.get(
            f"{self.get_detail_endpoint(key=site_page.slug, site_slug=site.slug)}"
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["widgets"]) == 3

        # Check that the widgets have been re-arranged based on the order field in the API response.
        assert response_data["widgets"][0]["id"] == str(widget_two.id)
        assert response_data["widgets"][1]["id"] == str(widget_three.id)
        assert response_data["widgets"][2]["id"] == str(widget_one.id)

    @pytest.mark.django_db
    def test_detail_widget_order_in_multiple_lists(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site, widget_list_one, widget_list_two, widgets = setup_widget_list()

        # Create a site page with the widget list
        site_page = factories.SitePageFactory.create(
            site=site, visibility=Visibility.PUBLIC, widgets=widget_list_two
        )

        # Check the widget list orders and add a widget from widget_list_one to widget_list_two with a different order
        update_widget_list_order(widgets, widget_list_two)

        response = self.client.get(
            f"{self.get_detail_endpoint(key=site_page.slug, site_slug=site.slug)}"
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["widgets"]) == 4

        # Check that the homepage uses the order in widget_list_two for widget_one
        assert response_data["widgets"][0]["id"] == str(widgets[0].id)
        assert response_data["widgets"][1]["id"] == str(widgets[5].id)
        assert response_data["widgets"][2]["id"] == str(widgets[3].id)
        assert response_data["widgets"][3]["id"] == str(widgets[4].id)

        # Update the homepage to widget_list_one
        site_page.widgets = widget_list_one
        site_page.save()

        response = self.client.get(
            f"{self.get_detail_endpoint(key=site_page.slug, site_slug=site.slug)}"
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["widgets"]) == 3

        # Check that the homepage uses the order in widget_list_one for widget_one
        assert response_data["widgets"][0]["id"] == str(widgets[1].id)
        assert response_data["widgets"][1]["id"] == str(widgets[2].id)
        assert response_data["widgets"][2]["id"] == str(widgets[0].id)
