import json

import pytest

import backend.tests.factories.access
from backend.models.constants import AppRole, Role, Visibility
from backend.models.sites import Language
from backend.tests import factories
from backend.tests.factories.access import get_anonymous_user, get_non_member_user

from .base_api_test import BaseApiTest, ReadOnlyApiTests
from .base_media_test import MediaTestMixin


class TestLanguagesEndpoints(MediaTestMixin, ReadOnlyApiTests, BaseApiTest):
    """
    End-to-end tests that the languages endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:language-list"
    API_DETAIL_VIEW = "api:language-detail"

    model = Language

    content_type = "application/json"

    def create_minimal_instance(self, visibility):
        return factories.LanguageFactory.create()

    @pytest.mark.django_db
    def test_list_empty(self):
        """Overriding the base test due to lack of pagination"""
        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 0

    @pytest.mark.django_db
    def test_list_minimal(self):
        """
        Overriding the base test to check custom permissions and the "other" language grouping
        """
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

        assert response_data[2]["language"] == "More FirstVoices Sites"
        assert response_data[2]["languageCode"] == ""
        assert len(response_data[2]["sites"]) == 2

        site_json = response_data[0]["sites"][0]
        assert site_json == {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": language0.title,
            "visibility": "public",
            "logo": None,
            "url": f"http://testserver/api/1.0/sites/{site.slug}",
            "enabledFeatures": [],
            "isHidden": False,
        }

    def get_expected_response(self, instance):
        sites_json = [self.get_expected_site_response(s) for s in instance.sites.all()]

        return {
            "language": instance.title,
            "languageCode": instance.language_code,
            "sites": sites_json,
        }

    def get_expected_site_response(self, site):
        return {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": site.language.title,
            "visibility": "public",
            "logo": None,
            "url": f"http://testserver/api/1.0/sites/{site.slug}",
            "enabledFeatures": [],
        }

    def generate_test_sites(self):
        # a language with sites of all visibilities
        all_vis_language = backend.tests.factories.access.LanguageFactory.create()
        team_site0 = factories.SiteFactory(
            language=all_vis_language, visibility=Visibility.TEAM
        )
        member_site0 = factories.SiteFactory(
            language=all_vis_language, visibility=Visibility.MEMBERS
        )
        public_site0 = factories.SiteFactory(
            language=all_vis_language, visibility=Visibility.PUBLIC
        )

        # languages with one site each
        team_language = backend.tests.factories.access.LanguageFactory.create()
        team_site1 = factories.SiteFactory(
            language=team_language, visibility=Visibility.TEAM
        )

        member_language = backend.tests.factories.access.LanguageFactory.create()
        member_site1 = factories.SiteFactory(
            language=member_language, visibility=Visibility.MEMBERS
        )

        public_language = backend.tests.factories.access.LanguageFactory.create()
        public_site1 = factories.SiteFactory(
            language=public_language, visibility=Visibility.PUBLIC
        )

        # sites with no language
        team_site2 = factories.SiteFactory(language=None, visibility=Visibility.TEAM)
        member_site2 = factories.SiteFactory(
            language=None, visibility=Visibility.MEMBERS
        )
        public_site2 = factories.SiteFactory(
            language=None, visibility=Visibility.PUBLIC
        )

        return {
            "public": [public_site0, public_site1, public_site2],
            "members": [member_site0, member_site1, member_site2],
            "team": [team_site0, team_site1, team_site2],
        }

    def assert_visible_sites(self, response, sites):
        assert response.status_code == 200
        response_data = json.loads(response.content)

        response_sites = [
            site["id"] for language in response_data for site in language["sites"]
        ]

        assert len(response_sites) == 6, "included extra sites"

        assert str(sites["members"][0].id) in response_sites
        assert str(sites["members"][1].id) in response_sites
        assert str(sites["members"][2].id) in response_sites

        assert str(sites["public"][0].id) in response_sites
        assert str(sites["public"][1].id) in response_sites
        assert str(sites["public"][2].id) in response_sites

    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.django_db
    def test_list_permissions_for_non_members(self, get_user):
        sites = self.generate_test_sites()

        user = get_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        self.assert_visible_sites(response, sites)

    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_list_permissions_for_members(self, role):
        sites = self.generate_test_sites()

        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=sites["team"][0], role=role)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        self.assert_visible_sites(response, sites)

    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_list_permissions_for_superadmins(self, role):
        sites = self.generate_test_sites()

        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        self.assert_visible_sites(response, sites)

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
