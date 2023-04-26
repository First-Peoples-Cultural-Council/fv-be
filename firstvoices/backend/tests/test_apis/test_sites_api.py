import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from .base_api_test import BaseApiTest


class TestSitesEndpoints(BaseApiTest):
    """
    End-to-end tests that the sites endpoints have the expected behaviour. Data formatting is checked in the
    serializer tests.
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

        language0 = factories.LanguageFactory.create(title="Language 0")
        site = factories.SiteFactory(language=language0, visibility=Visibility.PUBLIC)
        factories.SiteFactory(language=language0, visibility=Visibility.MEMBERS)

        language1 = factories.LanguageFactory.create(title="Language 1")
        factories.SiteFactory(language=language1, visibility=Visibility.MEMBERS)

        factories.LanguageFactory.create()

        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data) == 2

        assert response_data[0]["language"] == "Language 0"
        assert len(response_data[0]["sites"]) == 2

        assert response_data[1]["language"] == "Language 1"
        assert len(response_data[1]["sites"]) == 1

        site_json = response_data[0]["sites"][0]
        assert site_json == {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": language0.title,
            "visibility": "Public",
            "url": f"http://testserver/api/1.0/sites/{site.slug}/",
        }

    @pytest.mark.django_db
    def test_list_permissions(self):
        language0 = factories.LanguageFactory.create()
        team_site = factories.SiteFactory(
            language=language0, visibility=Visibility.TEAM
        )

        language1 = factories.LanguageFactory.create()
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

    @pytest.mark.django_db
    def test_detail(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language = factories.LanguageFactory.create()
        site = factories.SiteFactory.create(
            language=language, visibility=Visibility.MEMBERS
        )
        menu = factories.SiteMenuFactory.create(site=site, json='{"some": "json"}')

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": language.title,
            "visibility": "Members",
            "url": f"http://testserver/api/1.0/sites/{site.slug}/",
            "menu": menu.json,
            "features": [],
            "dictionary": f"http://testserver/api/1.0/sites/{site.slug}/dictionary/",
        }

    @pytest.mark.django_db
    def test_detail_default_site_menu(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        menu = factories.AppJsonFactory.create(
            key="default_site_menu", json='{"some": "json"}'
        )

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
                "key": enabled_feature.key,
                "isEnabled": True,
            }
        ]

    @pytest.mark.django_db
    def test_detail_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.get_detail_endpoint(site.slug)}")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(site.id)

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
