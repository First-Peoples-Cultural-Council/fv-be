import json

import pytest

import backend.tests.factories.access
from backend.models import AppJson
from backend.models.constants import Role, Visibility
from backend.tests import factories

from .base_api_test import BaseApiTest
from .base_media_test import MediaTestMixin


class TestSitesEndpoints(MediaTestMixin, BaseApiTest):
    """
    End-to-end tests that the sites endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:site-list"
    API_DETAIL_VIEW = "api:site-detail"

    @pytest.mark.django_db
    def test_list_empty(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 0

    @pytest.mark.django_db
    def test_list_full(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language0 = backend.tests.factories.access.LanguageFactory.create(
            title="Language 0"
        )
        site = factories.SiteFactory(language=language0, visibility=Visibility.PUBLIC)
        factories.SiteFactory(language=language0, visibility=Visibility.MEMBERS)

        language1 = backend.tests.factories.access.LanguageFactory.create(
            title="Language 1"
        )
        factories.SiteFactory(language=language1, visibility=Visibility.MEMBERS)

        # sites with no language set
        factories.SiteFactory(language=None, visibility=Visibility.PUBLIC)
        factories.SiteFactory(language=None, visibility=Visibility.MEMBERS)

        backend.tests.factories.access.LanguageFactory.create()

        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data) == 3

        assert response_data[0]["language"] == language0.title
        assert response_data[0]["languageCode"] == language0.language_code
        assert len(response_data[0]["sites"]) == 2

        assert response_data[1]["language"] == language1.title
        assert response_data[1]["languageCode"] == language1.language_code
        assert len(response_data[1]["sites"]) == 1

        assert response_data[2]["language"] == "Other"
        assert response_data[2]["languageCode"] == ""
        assert len(response_data[2]["sites"]) == 2

        site_json = response_data[0]["sites"][0]
        assert site_json == {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": language0.title,
            "visibility": "Public",
            "logo": None,
            "url": f"http://testserver/api/1.0/sites/{site.slug}",
            "features": [],
        }

    @pytest.mark.django_db
    def test_list_permissions(self):
        language0 = backend.tests.factories.access.LanguageFactory.create()
        team_site = factories.SiteFactory(
            language=language0, visibility=Visibility.TEAM
        )

        language1 = backend.tests.factories.access.LanguageFactory.create()
        factories.SiteFactory(language=language1, visibility=Visibility.TEAM)

        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=team_site, role=Role.ASSISTANT
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data) == 1, "did not filter out blocked site"
        assert (
            len(response_data[0]["sites"]) == 1
        ), "did not include available Team site"

    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_list_logo_from_same_site(self, visibility):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=visibility)
        image = factories.ImageFactory(site=site)
        site.logo = image
        site.save()

        response = self.client.get(f"{self.get_list_endpoint()}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 1
        assert len(response_data[0]["sites"]) == 1
        assert response_data[0]["sites"][0]["logo"] == self.get_expected_image_data(
            image
        )

    @pytest.mark.parametrize(
        "visibility, expected_visibility",
        [(Visibility.PUBLIC, "Public"), (Visibility.MEMBERS, "Members")],
    )
    @pytest.mark.django_db
    def test_detail(self, visibility, expected_visibility):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language = backend.tests.factories.access.LanguageFactory.create()
        site = factories.SiteFactory.create(language=language, visibility=visibility)
        menu = factories.SiteMenuFactory.create(site=site, json='{"some": "json"}')

        response = self.client.get(self.get_detail_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        site_url = f"http://testserver/api/1.0/sites/{site.slug}"
        assert response_data == {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": language.title,
            "visibility": expected_visibility,
            "url": site_url,
            "menu": menu.json,
            "features": [],
            "logo": None,
            "bannerImage": None,
            "bannerVideo": None,
            "homepage": None,
            "audio": f"{site_url}/audio",
            "categories": f"{site_url}/categories",
            "characters": f"{site_url}/characters",
            "data": f"{site_url}/data",
            "dictionary": f"{site_url}/dictionary",
            "dictionaryCleanup": f"{site_url}/dictionary-cleanup",
            "dictionaryCleanupPreview": f"{site_url}/dictionary-cleanup/preview",
            "ignoredCharacters": f"{site_url}/ignored-characters",
            "images": f"{site_url}/images",
            "people": f"{site_url}/people",
            "songs": f"{site_url}/songs",
            "videos": f"{site_url}/videos",
            "widgets": f"{site_url}/widgets",
            "wordOfTheDay": f"{site_url}/word-of-the-day",
        }

    @pytest.mark.django_db
    def test_detail_default_site_menu(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        menu = AppJson.objects.get(key="default_site_menu")

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["menu"] == menu.json

    @pytest.mark.django_db
    def test_detail_enabled_features(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        enabled_feature = factories.SiteFeatureFactory.create(
            site=site, key="key1", is_enabled=True
        )
        factories.SiteFeatureFactory.create(site=site, key="key2", is_enabled=False)

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["features"] == [
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
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS, logo=image)

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["logo"] == self.get_expected_image_data(image)

    @pytest.mark.django_db
    def test_detail_banner_image(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        image = factories.ImageFactory()
        site = factories.SiteFactory.create(
            visibility=Visibility.MEMBERS, banner_image=image
        )

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["bannerImage"] == self.get_expected_image_data(image)

    @pytest.mark.django_db
    def test_detail_banner_video(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        video = factories.VideoFactory()
        site = factories.SiteFactory.create(
            visibility=Visibility.MEMBERS, banner_video=video
        )

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

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

        widget_one = widget_list.widgets.all()[0]
        widget_two = widget_list.widgets.all()[1]
        widget_one.site = site
        widget_one.save()
        widget_two.site = site
        widget_two.save()

        widget_one_settings_one = factories.WidgetSettingsFactory.create(
            widget=widget_one
        )
        widget_one_settings_two = factories.WidgetSettingsFactory.create(
            widget=widget_one
        )
        widget_two_settings_one = factories.WidgetSettingsFactory.create(
            widget=widget_two
        )

        site.homepage = widget_list
        site.save()

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["homepage"]) == 2

        response_widget_one = response_data["homepage"][0]
        response_widget_two = response_data["homepage"][1]

        assert response_widget_one == {
            "id": str(widget_one.id),
            "title": widget_one.title,
            "widgetType": widget_one.widget_type,
            "format": "Default",
            "visibility": "Public",
            "settings": [
                {
                    "key": widget_one_settings_one.key,
                    "value": widget_one_settings_one.value,
                },
                {
                    "key": widget_one_settings_two.key,
                    "value": widget_one_settings_two.value,
                },
            ],
        }
        assert response_widget_two == {
            "id": str(widget_two.id),
            "title": widget_two.title,
            "widgetType": widget_two.widget_type,
            "format": "Default",
            "visibility": "Public",
            "settings": [
                {
                    "key": widget_two_settings_one.key,
                    "value": widget_two_settings_one.value,
                }
            ],
        }

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
        user = factories.UserFactory.create(id=1)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        if user_role is not None:
            factories.MembershipFactory.create(user=user, site=site, role=user_role)

        widget_list = factories.SiteWidgetListWithEachWidgetVisibilityFactory.create(
            site=site
        )
        widget_public = widget_list.widgets.all()[0]
        widget_members = widget_list.widgets.all()[1]
        widget_team = widget_list.widgets.all()[2]
        widget_public.site = site
        widget_public.save()
        widget_members.site = site
        widget_members.save()
        widget_team.site = site
        widget_team.save()

        site.homepage = widget_list
        site.save()

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")
        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert len(response_data["homepage"]) == expected_visible_widgets

    @pytest.mark.django_db
    def test_detail_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["slug"] == str(site.slug)

    @pytest.mark.django_db
    def test_detail_403(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_detail_404(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint('fake-site')}")

        assert response.status_code == 404

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
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(site.slug)}", format="json", data=req_body
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
        }
        response = self.client.put(
            f"{self.get_detail_endpoint(site1.slug)}", format="json", data=req_body
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)

        assert response_data["logo"] == ["Must be in the same site."]
