import json

import pytest
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.management import call_command

from backend.models import AppJson, Site
from backend.models.constants import AppRole, Role, Visibility
from backend.models.widget import SiteWidget, SiteWidgetListOrder
from backend.tests import factories
from backend.tests.factories.access import get_anonymous_user, get_non_member_user
from backend.tests.test_apis.base.base_media_test import MediaTestMixin
from backend.tests.test_apis.base.base_non_site_api import ReadOnlyNonSiteApiTest
from backend.tests.utils import (
    setup_widget_list,
    update_widget_list_order,
    update_widget_sites,
)


class TestSitesEndpoints(MediaTestMixin, ReadOnlyNonSiteApiTest):
    """
    End-to-end tests that the sites endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:site-list"
    API_DETAIL_VIEW = "api:site-detail"

    model = Site

    content_type = "application/json"

    def get_detail_endpoint(self, key):
        """Override to get urls based on site slugs instead of IDs"""
        try:
            site = Site.objects.all().filter(pk=key)

            if site.count() > 0:
                return super().get_detail_endpoint(site.first().slug)
        except ValidationError:
            # Allows creating malformed or fake URLs for testing
            pass

        return super().get_detail_endpoint(key)

    def create_minimal_instance(self, visibility=Visibility.PUBLIC):
        return factories.SiteFactory.create(visibility=visibility)

    def get_expected_list_response_item(self, site):
        return {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": str(site.language.title),
            "visibility": "public",
            "logo": None,
            "url": f"http://testserver/api/1.0/sites/{site.slug}",
            "enabledFeatures": [],
            "isHidden": False,
        }

    def get_site_menu(self, site):
        try:
            return site.menu
        except ObjectDoesNotExist:
            return AppJson.objects.get(key="default_site_menu")

    def get_expected_detail_response(self, site):
        site_url = f"http://testserver/api/1.0/sites/{site.slug}"

        return {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": site.language.title,
            "visibility": "public",
            "url": site_url,
            "menu": self.get_site_menu(site).json,
            "enabledFeatures": [],
            "isHidden": False,
            "logo": None,
            "bannerImage": None,
            "bannerVideo": None,
            "homepage": None,
            "audio": f"{site_url}/audio",
            "bulkVisibility": f"{site_url}/bulk-visibility",
            "categories": f"{site_url}/categories",
            "characters": f"{site_url}/characters",
            "dictionary": f"{site_url}/dictionary",
            "dictionaryCleanup": f"{site_url}/dictionary-cleanup",
            "dictionaryCleanupPreview": f"{site_url}/dictionary-cleanup/preview",
            "documents": f"{site_url}/documents",
            "features": f"{site_url}/features",
            "galleries": f"{site_url}/galleries",
            "ignoredCharacters": f"{site_url}/ignored-characters",
            "images": f"{site_url}/images",
            "immersionLabels": f"{site_url}/immersion-labels",
            "joinRequests": f"{site_url}/join-requests",
            "memberships": f"{site_url}/memberships",
            "mtdData": f"{site_url}/mtd-data",
            "pages": f"{site_url}/pages",
            "people": f"{site_url}/people",
            "songs": f"{site_url}/songs",
            "stats": f"{site_url}/stats",
            "stories": f"{site_url}/stories",
            "videos": f"{site_url}/videos",
            "widgets": f"{site_url}/widgets",
            "wordOfTheDay": f"{site_url}/word-of-the-day",
        }

    def generate_test_sites(self):
        # sites of all visibilities
        team_site = factories.SiteFactory(visibility=Visibility.TEAM)
        member_site = factories.SiteFactory(visibility=Visibility.MEMBERS)
        public_site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        hidden_site = factories.SiteFactory(
            visibility=Visibility.PUBLIC, is_hidden=True
        )

        return {
            "public": public_site,
            "members": member_site,
            "team": team_site,
            "hidden": hidden_site,
        }

    def assert_visible_sites_public(self, response, sites):
        assert response.status_code == 200
        response_data = json.loads(response.content)

        response_sites = [site["id"] for site in response_data["results"]]

        assert len(response_sites) == 1
        assert str(sites["public"].id) in response_sites

        assert str(sites["members"].id) not in response_sites
        assert str(sites["team"].id) not in response_sites
        assert str(sites["hidden"].id) not in response_sites

    def assert_visible_sites_members(self, response, sites):
        assert response.status_code == 200
        response_data = json.loads(response.content)

        response_sites = [site["id"] for site in response_data["results"]]

        assert len(response_sites) == 2
        assert str(sites["public"].id) in response_sites
        assert str(sites["members"].id) in response_sites

        assert str(sites["team"].id) not in response_sites
        assert str(sites["hidden"].id) not in response_sites

    def assert_visible_sites_team(self, response, sites):
        assert response.status_code == 200
        response_data = json.loads(response.content)

        response_sites = [site["id"] for site in response_data["results"]]

        assert len(response_sites) == 2
        assert str(sites["public"].id) in response_sites
        assert str(sites["team"].id) in response_sites

        assert str(sites["members"].id) not in response_sites
        assert str(sites["hidden"].id) not in response_sites

    def assert_visible_sites_staff(self, response, sites):
        assert response.status_code == 200
        response_data = json.loads(response.content)

        response_sites = [site["id"] for site in response_data["results"]]

        assert len(response_sites) == 4
        assert str(sites["public"].id) in response_sites
        assert str(sites["members"].id) in response_sites
        assert str(sites["team"].id) in response_sites
        assert str(sites["hidden"].id) in response_sites

    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.django_db
    def test_list_permissions_for_non_members(self, get_user):
        sites = self.generate_test_sites()

        user = get_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        self.assert_visible_sites_public(response, sites)

    @pytest.mark.django_db
    def test_list_permissions_for_members(self):
        sites = self.generate_test_sites()

        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=sites["members"], role=Role.MEMBER
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        self.assert_visible_sites_members(response, sites)

    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_list_permissions_for_team(self, role):
        sites = self.generate_test_sites()

        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=sites["team"], role=role)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        self.assert_visible_sites_team(response, sites)

    @pytest.mark.parametrize("staff_role", [AppRole.STAFF, AppRole.SUPERADMIN])
    @pytest.mark.django_db
    def test_list_permissions_for_staff(self, staff_role):
        sites = self.generate_test_sites()

        user = factories.get_app_admin(staff_role)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        self.assert_visible_sites_staff(response, sites)

    @pytest.mark.django_db
    def test_list_logo_from_same_site(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        image = factories.ImageFactory(site=site)
        site.logo = image
        site.save()

        response = self.client.get(f"{self.get_list_endpoint()}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"][0]["logo"] == self.get_expected_image_data(
            image
        )

    @pytest.mark.django_db
    def test_detail_default_site_menu(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        menu = AppJson.objects.get(key="default_site_menu")

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["menu"] == menu.json

    @pytest.mark.django_db
    @pytest.mark.parametrize("key", ["has_app", "HAS_APP", "Has_App"])
    def test_detail_app_site_menu(self, key):
        call_command("loaddata", "appjson-has_app.json", app_label="backend")
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.SiteFeatureFactory.create(site=site, key=key, is_enabled=True)
        menu = AppJson.objects.get(key="has_app_site_menu")

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["menu"] == menu.json

    @pytest.mark.django_db
    def test_detail_enabled_features(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        enabled_feature = factories.SiteFeatureFactory.create(
            site=site, key="key1", is_enabled=True
        )
        factories.SiteFeatureFactory.create(site=site, key="key2", is_enabled=False)

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["enabledFeatures"] == [
            {
                "id": str(enabled_feature.id),
                "key": enabled_feature.key,
                "isEnabled": True,
            }
        ]

    @pytest.mark.django_db
    def test_detail_logo_from_other_site(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        image = factories.ImageFactory()
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC, logo=image)

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["logo"] == self.get_expected_image_data(image)

    @pytest.mark.django_db
    def test_detail_banner_image(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        image = factories.ImageFactory()
        site = factories.SiteFactory.create(
            visibility=Visibility.PUBLIC, banner_image=image
        )

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["bannerImage"] == self.get_expected_image_data(image)

    @pytest.mark.django_db
    def test_detail_banner_video(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        video = factories.VideoFactory()
        site = factories.SiteFactory.create(
            visibility=Visibility.PUBLIC, banner_video=video
        )

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["bannerVideo"] == self.get_expected_video_data(video)

    @pytest.mark.django_db
    def test_detail_homepage(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.SiteWidgetListOrderFactory.reset_sequence()
        widget_list = factories.SiteWidgetListWithTwoWidgetsFactory.create(site=site)

        widget_one = widget_list.widgets.order_by("title").all()[0]
        widget_two = widget_list.widgets.order_by("title").all()[1]
        update_widget_sites(site, [widget_one, widget_two])

        widget_one_settings = factories.WidgetSettingsFactory.create(widget=widget_one)
        widget_two_settings = factories.WidgetSettingsFactory.create(widget=widget_two)

        site.homepage = widget_list
        site.save()

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["homepage"]) == 2

        # assert that widget one id is in the list
        assert str(widget_one.id) in [
            widget["id"] for widget in response_data["homepage"]
        ]
        # get the widget one object from the list
        response_widget_one = [
            widget
            for widget in response_data["homepage"]
            if widget["id"] == str(widget_one.id)
        ][0]

        # assert that widget two id is in the list
        assert str(widget_two.id) in [
            widget["id"] for widget in response_data["homepage"]
        ]
        # get the widget two object from the list
        response_widget_two = [
            widget
            for widget in response_data["homepage"]
            if widget["id"] == str(widget_two.id)
        ][0]

        def get_expected_widget_response(widget_instance, widget_settings):
            return {
                "created": widget_instance.created.astimezone().isoformat(),
                "createdBy": widget_instance.created_by.email,
                "lastModified": widget_instance.last_modified.astimezone().isoformat(),
                "lastModifiedBy": widget_instance.last_modified_by.email,
                "systemLastModified": widget_instance.system_last_modified.astimezone().isoformat(),
                "systemLastModifiedBy": widget_instance.system_last_modified_by.email,
                "id": str(widget_instance.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}/widgets/{str(widget_instance.id)}",
                "title": widget_instance.title,
                "site": {
                    "id": str(site.id),
                    "url": f"http://testserver/api/1.0/sites/{site.slug}",
                    "title": site.title,
                    "slug": site.slug,
                    "visibility": widget_instance.site.get_visibility_display().lower(),
                    "language": site.language.title,
                },
                "visibility": widget_instance.get_visibility_display().lower(),
                "type": widget_instance.widget_type,
                "format": "Default",
                "settings": [
                    {
                        "key": widget_settings.key,
                        "value": widget_settings.value,
                    },
                ],
            }

        assert response_widget_one == get_expected_widget_response(
            widget_one, widget_one_settings
        )
        assert response_widget_two == get_expected_widget_response(
            widget_two, widget_two_settings
        )

    @pytest.mark.django_db
    def test_detail_homepage_order(self):
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

        site.homepage = widget_list
        site.save()

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

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["homepage"]) == 3

        # Check that the widgets have been re-arranged based on the order field in the API response.
        assert response_data["homepage"][0]["id"] == str(widget_two.id)
        assert response_data["homepage"][1]["id"] == str(widget_three.id)
        assert response_data["homepage"][2]["id"] == str(widget_one.id)

    @pytest.mark.django_db
    def test_detail_homepage_order_in_multiple_lists(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site, widget_list_one, widget_list_two, widgets = setup_widget_list()

        # Set the site homepage widget list
        site.homepage = widget_list_two
        site.save()

        # Check the widget list orders and add a widget from widget_list_one to widget_list_two with a different order
        update_widget_list_order(widgets, widget_list_two)

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["homepage"]) == 4

        # Check that the homepage uses the order in widget_list_two for widget_one
        assert response_data["homepage"][0]["id"] == str(widgets[0].id)
        assert response_data["homepage"][1]["id"] == str(widgets[5].id)
        assert response_data["homepage"][2]["id"] == str(widgets[3].id)
        assert response_data["homepage"][3]["id"] == str(widgets[4].id)

        # Update the homepage to widget_list_one
        site.homepage = widget_list_one
        site.save()

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["homepage"]) == 3

        # Check that the homepage uses the order in widget_list_one for widget_one
        assert response_data["homepage"][0]["id"] == str(widgets[1].id)
        assert response_data["homepage"][1]["id"] == str(widgets[2].id)
        assert response_data["homepage"][2]["id"] == str(widgets[0].id)

    @pytest.mark.parametrize(
        "user_role, expected_visible_widgets",
        [
            (None, 1),
            (Role.MEMBER, 2),
            (Role.ASSISTANT, 3),
            (Role.EDITOR, 3),
            (Role.LANGUAGE_ADMIN, 3),
        ],
    )
    @pytest.mark.django_db
    def test_detail_homepage_permissions(self, user_role, expected_visible_widgets):
        user = factories.UserFactory.create()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        if user_role is not None:
            factories.MembershipFactory.create(user=user, site=site, role=user_role)

        widget_list = factories.SiteWidgetListWithEachWidgetVisibilityFactory.create(
            site=site
        )
        widget_public = widget_list.widgets.order_by("title").all()[0]
        widget_members = widget_list.widgets.order_by("title").all()[1]
        widget_team = widget_list.widgets.order_by("title").all()[2]
        update_widget_sites(site, [widget_public, widget_members, widget_team])

        site.homepage = widget_list
        site.save()

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["homepage"]) == expected_visible_widgets

    @pytest.mark.django_db
    def test_detail_member_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.MEMBER)
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["slug"] == str(site.slug)

    @pytest.mark.django_db
    def test_detail_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["slug"] == str(site.slug)

    @pytest.mark.django_db
    def test_detail_403(self):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint(site.id)}")

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_detail_404(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint('fake-site')}")

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_update_confirm_user(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        image = factories.ImageFactory.create(site=site)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )

        self.client.force_authenticate(user=user)
        req_body = {
            "title": site.title,
            "logo": None,
            "bannerImage": str(image.id),
            "bannerVideo": None,
            "homepage": [],
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(site.id)}", format="json", data=req_body
        )

        assert response.status_code == 200

        updated_site = Site.objects.get(id=site.id)
        assert updated_site.created == site.created
        assert updated_site.last_modified > site.last_modified
        assert updated_site.system_last_modified > site.system_last_modified
        assert updated_site.created_by.email == site.created_by.email
        assert updated_site.system_last_modified_by.email == user.email
        assert updated_site.last_modified_by.email == user.email

    @pytest.mark.django_db
    def test_update_media(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        image = factories.ImageFactory.create(site=site)
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )

        self.client.force_authenticate(user=user)
        req_body = {
            "title": site.title,
            "logo": str(image.id),
            "bannerImage": None,
            "bannerVideo": None,
            "homepage": [],
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(site.id)}", format="json", data=req_body
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["logo"]["id"] == str(image.id)

    @pytest.mark.django_db
    def test_invalid_media_source(self):
        # Internally the function used to verify source of all 3 media items supplied is the same,
        # testing out only for the logo
        site1 = factories.SiteFactory.create(visibility=Visibility.TEAM)
        site2 = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        image = factories.ImageFactory.create(site=site2)
        factories.MembershipFactory.create(
            user=user, site=site1, role=Role.LANGUAGE_ADMIN
        )

        self.client.force_authenticate(user=user)
        req_body = {
            "title": site1.title,
            "logo": str(image.id),
            "bannerImage": None,
            "bannerVideo": None,
            "homepage": [],
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(site1.slug)}", format="json", data=req_body
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)

        assert response_data["logo"] == ["Must be in the same site."]

    @pytest.mark.django_db
    def test_update_homepage_no_existing(self):
        site = factories.SiteFactory.create()
        user = factories.get_non_member_user()

        widget_one = factories.SiteWidgetFactory.create(site=site)
        widget_one_settings = factories.WidgetSettingsFactory.create(widget=widget_one)
        widget_two = factories.SiteWidgetFactory.create(site=site)

        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )

        assert site.homepage is None

        self.client.force_authenticate(user=user)
        req_body = {
            "logo": None,
            "bannerImage": None,
            "bannerVideo": None,
            "homepage": [str(widget_two.id), str(widget_one.id)],
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(site.id)}", format="json", data=req_body
        )
        response_data = json.loads(response.content)

        expected_widget_one_settings = [
            {"key": widget_one_settings.key, "value": widget_one_settings.value}
        ]

        assert response.status_code == 200
        assert response_data["homepage"][0]["id"] == str(widget_two.id)
        assert response_data["homepage"][1]["id"] == str(widget_one.id)
        assert response_data["homepage"][1]["settings"] == expected_widget_one_settings

    @pytest.mark.django_db
    def test_update_homepage_with_existing(self):
        site = factories.SiteFactory.create()
        user = factories.get_non_member_user()

        existing_list = factories.SiteWidgetListWithTwoWidgetsFactory.create(site=site)
        existing_widget_one = existing_list.widgets.order_by("title").all()[0]
        existing_widget_two = existing_list.widgets.order_by("title").all()[1]
        existing_widget_one_order_id = SiteWidgetListOrder.objects.get(
            site_widget=existing_widget_one
        ).id
        existing_widget_two_order_id = SiteWidgetListOrder.objects.get(
            site_widget=existing_widget_two
        ).id
        update_widget_sites(
            site,
            [
                existing_widget_one,
                existing_widget_two,
            ],
        )

        # Set a homepage for the site with some existing widgets.
        site.homepage = existing_list
        site.save()

        # Create a new widget and check that it is not in the site homepage list.
        widget_one = factories.SiteWidgetFactory.create(site=site)
        assert widget_one not in site.homepage.widgets.all()

        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )

        # Using the update API set the homepage to contain only the new widget.
        self.client.force_authenticate(user=user)
        req_body = {
            "logo": None,
            "bannerImage": None,
            "bannerVideo": None,
            "homepage": [str(widget_one.id)],
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(site.id)}", format="json", data=req_body
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        # Check that the site homepage contains the new widget
        assert response_data["homepage"][0]["id"] == str(widget_one.id)
        assert len(response_data["homepage"]) == 1
        updated_site = Site.objects.get(id=site.id)
        assert widget_one in updated_site.homepage.widgets.all()

        # Check that the homepage list is the same list (only widgets changed)
        assert updated_site.homepage.id == existing_list.id

        # Check that the existing widgets are not part of the new homepage
        current_widget_order_id_list = [
            order.id
            for order in SiteWidgetListOrder.objects.filter(
                site_widget__in=updated_site.homepage.widgets.all()
            )
        ]
        assert existing_widget_one_order_id not in current_widget_order_id_list
        assert existing_widget_two_order_id not in current_widget_order_id_list

        # Check that the old widget orders have been deleted
        assert (
            SiteWidgetListOrder.objects.filter(id=existing_widget_one_order_id).exists()
            is False
        )
        assert (
            SiteWidgetListOrder.objects.filter(id=existing_widget_two_order_id).exists()
            is False
        )

        # Check that the old widgets still exist
        assert SiteWidget.objects.filter(id=existing_widget_one.id).exists() is True
        assert SiteWidget.objects.filter(id=existing_widget_two.id).exists() is True

    @pytest.mark.django_db
    def test_detail_homepage_validation(self):
        site_one = factories.SiteFactory.create()
        site_two = factories.SiteFactory.create()
        user = factories.get_non_member_user()

        widget_one = factories.SiteWidgetFactory.create(site=site_one)
        widget_two = factories.SiteWidgetFactory.create(site=site_two)

        factories.MembershipFactory.create(
            user=user, site=site_one, role=Role.LANGUAGE_ADMIN
        )

        assert site_one.homepage is None

        self.client.force_authenticate(user=user)
        req_body = {
            "logo": None,
            "bannerImage": None,
            "bannerVideo": None,
            "homepage": [str(widget_two.id), str(widget_one.id)],
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(site_one.slug)}", format="json", data=req_body
        )

        assert response.status_code == 400

    def create_original_instance_for_patch(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC, title="Title")
        homepage = factories.SiteWidgetListWithTwoWidgetsFactory.create(site=site)
        logo = factories.ImageFactory.create(site=site)
        banner_image = factories.ImageFactory.create(site=site)

        site.logo = logo
        site.homepage = homepage
        site.banner_image = banner_image
        site.save()
        return site

    def get_updated_patch_instance(self, original_instance):
        return self.model.objects.filter(pk=original_instance.pk).first()

    def get_valid_patch_data(self, site=None):
        if site:
            banner_video = factories.VideoFactory.create(site=site)
        return {
            "banner_image": None,
            "banner_video": f"{str(banner_video.id)}" if site else None,
        }

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: Site
    ):
        assert updated_instance.title == original_instance.title
        assert updated_instance.logo == original_instance.logo
        assert updated_instance.homepage == original_instance.homepage
        assert updated_instance.visibility == original_instance.visibility
        assert updated_instance.id == original_instance.id
        assert updated_instance.slug == original_instance.slug
        assert updated_instance.created == original_instance.created
        assert updated_instance.last_modified > original_instance.last_modified
        assert (
            updated_instance.system_last_modified
            > original_instance.system_last_modified
        )

    def assert_patch_instance_updated_fields(self, data, updated_instance: Site):
        assert updated_instance.banner_image is None
        assert str(updated_instance.banner_video.id) == data["banner_video"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["title"] == original_instance.title
        assert (
            actual_response["visibility"]
            == original_instance.get_visibility_display().lower()
        )
        assert actual_response["logo"]["id"] == str(original_instance.logo.id)
        assert actual_response["homepage"][0]["id"] == str(
            original_instance.homepage.sitewidgetlistorder_set.first().site_widget_id
        )
        assert actual_response["bannerImage"] == data["banner_image"]
        assert actual_response["bannerVideo"]["id"] == data["banner_video"]
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["slug"] == original_instance.slug

    @pytest.mark.django_db
    def test_detail_patch_invalid_400(self):
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        instance = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.patch(
            f"{self.get_detail_endpoint(instance.slug)}",
            data=json.dumps(None),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_detail_patch_403(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        instance = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.patch(
            f"{self.get_detail_endpoint(instance.slug)}",
            data=json.dumps(self.get_valid_patch_data(instance)),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_patch_site_missing_404(self):
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.get_detail_endpoint(key="missing-instance"),
            data=json.dumps(self.get_valid_patch_data()),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_patch_success_200(self):
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        instance = self.create_original_instance_for_patch()
        data = self.get_valid_patch_data(instance)

        response = self.client.patch(
            f"{self.get_detail_endpoint(instance.slug)}",
            data=json.dumps(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(instance.id)

        updated_patch_instance = self.get_updated_patch_instance(instance)

        assert updated_patch_instance.created_by.email == instance.created_by.email
        assert updated_patch_instance.system_last_modified_by.email == user.email
        assert updated_patch_instance.last_modified_by.email == user.email

        self.assert_patch_instance_original_fields(instance, updated_patch_instance)
        self.assert_patch_instance_updated_fields(data, updated_patch_instance)
        self.assert_update_patch_response(instance, data, response_data)

    @pytest.mark.parametrize(
        "team_role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_hidden_sites_visible_in_list_only_to_team(self, team_role):
        user1 = factories.get_non_member_user()
        user2 = factories.get_non_member_user()

        site = factories.SiteFactory.create(
            visibility=Visibility.PUBLIC, is_hidden=True
        )
        factories.MembershipFactory.create(user=user1, site=site, role=team_role)
        factories.MembershipFactory.create(user=user2, site=site, role=Role.MEMBER)

        self.client.force_authenticate(user=user1)

        response = self.client.get(self.get_list_endpoint())
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 1

        self.client.force_authenticate(user=user2)

        response = self.client.get(self.get_list_endpoint())
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0

    @pytest.mark.django_db
    def test_hidden_site_detail_403(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        instance = factories.SiteFactory.create(
            visibility=Visibility.PUBLIC, is_hidden=True
        )

        response = self.client.get(f"{self.get_detail_endpoint(instance.slug)}")
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_hidden_site_detail_403_members(self):
        user = factories.get_non_member_user()
        instance = factories.SiteFactory.create(
            visibility=Visibility.PUBLIC, is_hidden=True
        )
        factories.MembershipFactory.create(user=user, site=instance, role=Role.MEMBER)
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint(instance.slug)}")
        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize("app_role", [AppRole.SUPERADMIN, AppRole.STAFF])
    def test_hidden_site_detail_staff(self, app_role):
        user = factories.get_app_admin(app_role)
        self.client.force_authenticate(user=user)
        instance = factories.SiteFactory.create(
            visibility=Visibility.PUBLIC, is_hidden=True
        )

        response = self.client.get(f"{self.get_detail_endpoint(instance.slug)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(instance.id)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_hidden_site_detail_team_member(self, role):
        instance = factories.SiteFactory.create(
            visibility=Visibility.PUBLIC, is_hidden=True
        )
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=instance, role=role)
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint(instance.slug)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(instance.id)
