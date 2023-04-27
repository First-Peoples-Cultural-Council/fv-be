import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from .base_api_test import BaseSiteContentApiTest


class TestIgnoredCharactersEndpoints(BaseSiteContentApiTest):
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:ignored_characters-list"
    API_DETAIL_VIEW = "api:ignored_characters-detail"

    @pytest.mark.django_db
    def test_site_not_found(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint("invalid-site"))

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_site_access_denied(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_list_empty(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_list_with_ignored_characters(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        ignored_character0 = factories.IgnoredCharacterFactory.create(
            title="/", site=site
        )
        factories.IgnoredCharacterFactory.create(title="-", site=site)

        response = self.client.get(self.get_list_endpoint(site.slug))
        print(response.request)

        assert response.status_code == 200

        response_data = json.loads(response.content)
        print(response_data)
        assert len(response_data["results"]) == 2
        assert response_data["count"] == 2

        ignored_character_json = response_data["results"][0]
        assert ignored_character_json == {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(ignored_character0.id))}",
            "id": str(ignored_character0.id),
            "title": "/",
            "site": site.title,
        }

    @pytest.mark.django_db
    def test_list_permissons(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)
        factories.IgnoredCharacterFactory.create(title="/", site=site)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 403

        factories.MembershipFactory(user=user, site=site, role=Role.LANGUAGE_ADMIN)
        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 1
        assert response_data["count"] == 1

    @pytest.mark.django_db
    def test_detail(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        ignored_character0 = factories.IgnoredCharacterFactory.create(
            title="/", site=site
        )

        response = self.client.get(
            self.get_detail_endpoint(
                site_slug=site.slug, key=str(ignored_character0.id)
            )
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(ignored_character0.id))}",
            "id": str(ignored_character0.id),
            "title": "/",
            "site": site.title,
        }

    @pytest.mark.django_db
    def test_detail_403(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)
        ignored_character = factories.IgnoredCharacterFactory.create(
            title="/", site=site
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(ignored_character.id))
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_detail_404(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        factories.IgnoredCharacterFactory.create(title="/", site=site)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key="invalid")
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detail_permissions(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)
        ignored_character = factories.IgnoredCharacterFactory.create(
            title="/", site=site
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(ignored_character.id))
        )

        assert response.status_code == 403

        factories.MembershipFactory(user=user, site=site, role=Role.LANGUAGE_ADMIN)
        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(ignored_character.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(ignored_character.id))}",
            "id": str(ignored_character.id),
            "title": "/",
            "site": site.title,
        }
