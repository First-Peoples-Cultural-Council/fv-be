import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from .base_api_test import BaseSiteControlledContentApiTest


class TestIgnoredCharactersEndpoints(BaseSiteControlledContentApiTest):
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:ignoredcharacter-list"
    API_DETAIL_VIEW = "api:ignoredcharacter-detail"

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
            "url": f"http://testserver{self.get_detail_endpoint(key=str(ignored_character0.id), site_slug=site.slug)}",
            "id": str(ignored_character0.id),
            "title": "/",
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
    def test_detail_403(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)
        ignored_character = factories.IgnoredCharacterFactory.create(
            title="/", site=site
        )

        response = self.client.get(
            self.get_detail_endpoint(key=str(ignored_character.id), site_slug=site.slug)
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_detail_404_site_not_found(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        ignored = factories.IgnoredCharacterFactory.create(title="/", site=site)

        response = self.client.get(
            self.get_detail_endpoint(key=ignored.id, site_slug="invalid")
        )

        assert response.status_code == 404

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
                key=str(ignored_character0.id), site_slug=site.slug
            )
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == {
            "url": f"http://testserver{self.get_detail_endpoint(key=str(ignored_character0.id), site_slug=site.slug)}",
            "id": str(ignored_character0.id),
            "title": "/",
        }

    @pytest.mark.django_db
    def test_detail_permissions(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)
        ignored_character = factories.IgnoredCharacterFactory.create(
            title="/", site=site
        )

        response = self.client.get(
            self.get_detail_endpoint(key=str(ignored_character.id), site_slug=site.slug)
        )

        assert response.status_code == 403

        factories.MembershipFactory(user=user, site=site, role=Role.LANGUAGE_ADMIN)
        response = self.client.get(
            self.get_detail_endpoint(key=str(ignored_character.id), site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {
            "url": f"http://testserver{self.get_detail_endpoint(key=str(ignored_character.id), site_slug=site.slug)}",
            "id": str(ignored_character.id),
            "title": "/",
        }
