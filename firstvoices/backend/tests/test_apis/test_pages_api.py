import json

import pytest

from backend.models import SitePage
from backend.models.constants import AppRole, Role, Visibility
from backend.models.widget import SiteWidget, SiteWidgetList, SiteWidgetListOrder
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseControlledLanguageAdminOnlySiteContentAPITest,
)
from backend.tests.utils import (
    setup_widget_list,
    update_widget_list_order,
    update_widget_sites,
)


class TestSitePageEndpoint(BaseControlledLanguageAdminOnlySiteContentAPITest):
    API_LIST_VIEW = "api:sitepage-list"
    API_DETAIL_VIEW = "api:sitepage-detail"

    model = SitePage

    def get_lookup_key(self, instance):
        return instance.slug

    def create_minimal_instance(self, site, visibility):
        return factories.SitePageFactory.create(site=site, visibility=visibility)

    def get_valid_data(self, site=None):
        widget_list = factories.SiteWidgetListWithThreeWidgetsFactory.create(site=site)
        widgets = SiteWidget.objects.filter(sitewidgetlist_set=widget_list)
        for widget in widgets:
            widget.site = site
            widget.save()
        widget_ids = list(map(lambda x: str(x.id), widget_list.widgets.all()))
        banner_image = factories.ImageFactory.create(site=site)

        return {
            "title": "Title",
            "visibility": "public",
            "subtitle": "Subtitle",
            "slug": "test-page-slug",  # required for create
            "widgets": widget_ids,
            "banner_image": str(banner_image.id),
            "banner_video": None,
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "Title",
            "visibility": "public",
            "slug": "test-page-slug",
        }

    def add_expected_defaults(self, data):
        return {
            **data,
            "subtitle": "",
            "widgets": [],
            "banner_image": None,
            "banner_video": None
        }

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        for order_item in instance.widgets.sitewidgetlistorder_set.all():
            self.assert_instance_deleted(order_item)
        self.assert_instance_deleted(instance.widgets)

    def assert_updated_instance(self, expected_data, actual_instance: SitePage):
        assert actual_instance.title == expected_data["title"]
        assert (
            actual_instance.get_visibility_display().lower()
            == expected_data["visibility"]
        )
        assert actual_instance.subtitle == expected_data["subtitle"]

        actual_widget_ids = [str(x["id"]) for x in actual_instance.widgets.widgets.values("id")]
        assert len(actual_widget_ids) == len(expected_data["widgets"])

        for index, actual_id in enumerate(actual_widget_ids):
            assert str(actual_id) == expected_data["widgets"][index]

        if expected_data["banner_image"]:
            assert str(actual_instance.banner_image.id) == expected_data["banner_image"]
        else:
            assert actual_instance.banner_image is None

        if expected_data["banner_video"]:
            assert str(actual_instance.banner_video.id) == expected_data["banner_video"]
        else:
            assert actual_instance.banner_video is None

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["visibility"] == expected_data["visibility"]
        assert actual_response["subtitle"] == expected_data["subtitle"]

        assert len(actual_response["widgets"]) == len(expected_data["widgets"])
        for i, w in enumerate(expected_data["widgets"]):
            assert actual_response["widgets"][i]["id"] == expected_data["widgets"][i]

        if expected_data["banner_image"]:
            assert actual_response["bannerImage"]["id"] == expected_data["banner_image"]
        else:
            assert actual_response["bannerImage"] is None

        if expected_data["banner_video"]:
            assert actual_response["bannerVideo"]["id"] == expected_data["banner_video"]
        else:
            assert actual_response["bannerVideo"] is None

    def get_expected_response(self, instance, site):
        controlled_standard_fields = self.get_expected_controlled_standard_fields(
            instance, site
        )
        controlled_standard_fields[
            "url"
        ] = f"http://testserver{self.get_detail_endpoint(key=instance.slug, site_slug=site.slug)}"
        return {
            **controlled_standard_fields,
            "subtitle": "",
            "slug": instance.slug,
        }

    def get_expected_detail_response(self, instance, site):
        controlled_standard_fields = self.get_expected_controlled_standard_fields(
            instance, site
        )
        controlled_standard_fields[
            "url"
        ] = f"http://testserver{self.get_detail_endpoint(key=instance.slug, site_slug=site.slug)}"
        return {
            **controlled_standard_fields,
            "subtitle": "",
            "slug": instance.slug,
            "widgets": [],
            "bannerImage": None,
            "bannerVideo": None,
        }

    def assert_created_instance(self, pk, data):
        instance = SitePage.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        assert actual_response["slug"] == expected_data["slug"]
        return self.assert_update_response(expected_data, actual_response)

    def create_original_instance_for_patch(self, site):
        widgets = factories.SiteWidgetListWithTwoWidgetsFactory.create(site=site)
        banner_image = factories.ImageFactory.create(site=site)
        return factories.SitePageFactory.create(
            site=site,
            title="Title",
            visibility=Visibility.PUBLIC,
            subtitle="Subtitle",
            widgets=widgets,
            banner_image=banner_image,
            banner_video=None,
        )

    def get_valid_patch_data(self, site=None):
        return {"visibility": "members"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: SitePage
    ):
        assert updated_instance.title == original_instance.title
        assert updated_instance.subtitle == original_instance.subtitle
        assert updated_instance.widgets == original_instance.widgets
        assert updated_instance.banner_image == original_instance.banner_image
        assert updated_instance.banner_video == original_instance.banner_video
        assert updated_instance.id == original_instance.id
        assert updated_instance.slug == original_instance.slug

    def assert_patch_instance_updated_fields(self, data, updated_instance: SitePage):
        assert updated_instance.get_visibility_display().lower() == data["visibility"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["title"] == original_instance.title
        assert actual_response["visibility"] == data["visibility"]
        assert actual_response["subtitle"] == original_instance.subtitle
        assert actual_response["widgets"][0]["id"] == str(
            original_instance.widgets.sitewidgetlistorder_set.first().site_widget_id
        )
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["slug"] == original_instance.slug

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

    @pytest.mark.django_db
    def test_detail_widget_order(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.SiteWidgetListOrderFactory.reset_sequence()
        widget_list = factories.SiteWidgetListWithThreeWidgetsFactory.create(site=site)

        # Get the widgets from the widget list
        widget_one = widget_list.widgets.order_by("title").all()[0]
        widget_two = widget_list.widgets.order_by("title").all()[1]
        widget_three = widget_list.widgets.order_by("title").all()[2]
        update_widget_sites(site, [widget_one, widget_two, widget_three])

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

    @pytest.mark.django_db
    def test_detail_widget_validation(self):
        site_one = factories.SiteFactory.create()
        site_two = factories.SiteFactory.create()
        user = factories.UserFactory.create()

        widget_one = factories.SiteWidgetFactory.create(site=site_one)
        widget_two = factories.SiteWidgetFactory.create(site=site_two)

        factories.MembershipFactory.create(
            user=user, site=site_one, role=Role.LANGUAGE_ADMIN
        )

        page = factories.SitePageFactory.create(site=site_one)

        self.client.force_authenticate(user=user)
        req_body = {
            "title": "Title",
            "visibility": "Public",
            "subtitle": "Subtitle",
            "slug": "page-slug",
            "widgets": [str(widget_two.id), str(widget_one.id)],
            "banner_image": None,
            "banner_video": None,
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(key=page.slug, site_slug=site_one.slug)}",
            format="json",
            data=req_body,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_detail_page_create(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        widget_one = factories.SiteWidgetFactory.create(site=site)
        widget_two = factories.SiteWidgetFactory.create(site=site)

        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 2
        assert len(SiteWidgetList.objects.all()) == 0
        assert len(SiteWidgetListOrder.objects.all()) == 0
        assert len(SitePage.objects.all()) == 0

        data = {
            "title": "Title",
            "visibility": "Public",
            "subtitle": "Subtitle",
            "slug": "test-page-one",
            "widgets": [str(widget_two.id), str(widget_one.id)],
            "banner_image": None,
            "banner_video": None,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        # Check that the correct number of model instances have been created.
        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 2
        assert len(SiteWidgetList.objects.all()) == 1
        assert len(SiteWidgetListOrder.objects.all()) == 2
        assert len(SitePage.objects.all()) == 1

        page = SitePage.objects.first()

        assert page.title == data["title"]
        assert page.get_visibility_display() == data["visibility"]
        assert page.subtitle == data["subtitle"]
        assert page.slug == data["slug"]
        assert len(page.widgets.widgets.all()) == 2

        # Check that the order value was created according to the order the widgets were passed to the API.
        widget_one_order = SiteWidgetListOrder.objects.get(
            site_widget__id=widget_one.id
        )
        widget_two_order = SiteWidgetListOrder.objects.get(
            site_widget__id=widget_two.id
        )
        assert widget_one_order.order == 1
        assert widget_two_order.order == 0

    @pytest.mark.django_db
    def test_detail_widget_create_no_widgets(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count
        assert len(SiteWidgetList.objects.all()) == 0
        assert len(SiteWidgetListOrder.objects.all()) == 0
        assert len(SitePage.objects.all()) == 0

        data = {
            "title": "Title",
            "visibility": "Public",
            "subtitle": "Subtitle",
            "slug": "test-page-one",
            "widgets": [],
            "banner_image": None,
            "banner_video": None,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        # Check that the correct number of model instances have been created.
        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count
        assert len(SiteWidgetList.objects.all()) == 1
        assert len(SiteWidgetListOrder.objects.all()) == 0
        assert len(SitePage.objects.all()) == 1

        page = SitePage.objects.first()

        assert page.title == data["title"]
        assert page.get_visibility_display() == data["visibility"]
        assert page.subtitle == data["subtitle"]
        assert page.slug == data["slug"]

    @pytest.mark.django_db
    def test_detail_page_update(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        widget_list = factories.SiteWidgetListWithThreeWidgetsFactory.create(site=site)
        page = factories.SitePageFactory.create(
            title="Test Title",
            visibility=Visibility.PUBLIC,
            subtitle="Test Subtitle",
            slug="test-page-one",
            site=site,
            widgets=widget_list,
        )

        new_widget_one = factories.SiteWidgetFactory.create(site=site)
        new_widget_two = factories.SiteWidgetFactory.create(site=site)

        data = {
            "title": "Test Title Updated",
            "visibility": "Team",
            "subtitle": "Test Subtitle Updated",
            "widgets": [str(new_widget_two.id), str(new_widget_one.id)],
            "banner_image": None,
            "banner_video": None,
        }

        assert len(page.widgets.widgets.all()) == 3
        assert len(SiteWidgetList.objects.all()) == 1
        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 2
        assert len(SiteWidgetListOrder.objects.all()) == 3
        assert len(SitePage.objects.all()) == 1

        response = self.client.put(
            self.get_detail_endpoint(key=page.slug, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        assert len(SiteWidgetList.objects.all()) == 1
        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count + 2
        assert len(SiteWidgetListOrder.objects.all()) == 2
        assert len(SitePage.objects.all()) == 1

        updated_page = SitePage.objects.get(id=page.id)

        assert updated_page.title == data["title"]
        assert updated_page.get_visibility_display() == data["visibility"]
        assert updated_page.subtitle == data["subtitle"]
        assert len(updated_page.widgets.widgets.all()) == 2

        # Check that the order value was created according to the order the widgets were passed to the API.
        widget_one_order = SiteWidgetListOrder.objects.get(
            site_widget__id=new_widget_one.id
        )
        widget_two_order = SiteWidgetListOrder.objects.get(
            site_widget__id=new_widget_two.id
        )
        assert widget_one_order.order == 1
        assert widget_two_order.order == 0

    @pytest.mark.django_db
    def test_detail_page_delete(self):
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        default_widgets_count = SiteWidget.objects.filter(site=site).count()

        widget_list = factories.SiteWidgetListWithThreeWidgetsFactory.create(site=site)
        page = factories.SitePageFactory.create(
            site=site, visibility=Visibility.PUBLIC, widgets=widget_list
        )

        assert SitePage.objects.filter(id=page.id).exists()
        assert SiteWidgetList.objects.filter(sitepage_set__id=page.id).exists()

        assert len(SiteWidgetList.objects.all()) == 1
        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count
        assert len(SiteWidgetListOrder.objects.all()) == 3
        assert len(SitePage.objects.all()) == 1

        response = self.client.delete(
            self.get_detail_endpoint(key=page.slug, site_slug=site.slug)
        )

        assert response.status_code == 204
        assert not SitePage.objects.filter(id=page.id).exists()
        assert not SiteWidgetList.objects.filter(sitepage_set__id=page.id).exists()

        assert len(SiteWidgetList.objects.all()) == 0
        assert len(SiteWidget.objects.filter(site=site)) == default_widgets_count
        assert len(SiteWidgetListOrder.objects.all()) == 0
        assert len(SitePage.objects.all()) == 0
