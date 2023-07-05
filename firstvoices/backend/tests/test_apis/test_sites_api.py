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

    @pytest.mark.django_db
    def test_detail(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language = backend.tests.factories.access.LanguageFactory.create()
        site = factories.SiteFactory.create(
            language=language, visibility=Visibility.MEMBERS
        )
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
            "visibility": "Members",
            "url": site_url,
            "menu": menu.json,
            "features": [],
            "logo": None,
            "bannerImage": None,
            "bannerVideo": None,
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
