import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import ReadOnlyApiTests


class TestMySitesEndpoint(ReadOnlyApiTests):
    """
    End to end tests that check the my-sites endpoint for expected behavior.
    """

    API_LIST_VIEW = "api:my-sites-list"
    API_DETAIL_VIEW = "api:my-sites-detail"
    APP_NAME = "backend"

    def create_minimal_instance(self, visibility):
        # a "my site" is a membership, so we also need a site and an authenticated user
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)
        return user.memberships.first()

    def get_expected_response(self, instance):
        return {
            "id": str(instance.site.id),
            "title": instance.site.title,
            "slug": instance.site.slug,
            "language": instance.site.language.title,
            "visibility": instance.site.get_visibility_display(),
            "logo": None,
            "url": f"http://testserver/api/1.0/my-sites/{instance.site.slug}",
            "features": [],
            "role": instance.get_role_display(),
        }

    @pytest.mark.django_db
    def test_no_membership(self):
        user = factories.UserFactory.create()
        factories.SiteFactory.create(visibility=Visibility.TEAM)
        factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_members_role(self):
        user = factories.UserFactory.create()
        factories.get_site_with_member(Visibility.TEAM, Role.MEMBER, user)
        factories.get_site_with_member(Visibility.MEMBERS, Role.MEMBER, user)
        factories.get_site_with_member(Visibility.PUBLIC, Role.MEMBER, user)

        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 2
        assert response_data["results"][0]["visibility"] == Visibility.MEMBERS.label
        assert response_data["results"][1]["visibility"] == Visibility.PUBLIC.label

    @pytest.mark.django_db
    def test_assistant_role(self):
        user = factories.UserFactory.create()
        factories.get_site_with_member(Visibility.TEAM, Role.ASSISTANT, user)
        factories.get_site_with_member(Visibility.MEMBERS, Role.ASSISTANT, user)
        factories.get_site_with_member(Visibility.PUBLIC, Role.ASSISTANT, user)

        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 3

    @pytest.mark.django_db
    def test_editor_role(self):
        user = factories.UserFactory.create()
        factories.get_site_with_member(Visibility.TEAM, Role.EDITOR, user)
        factories.get_site_with_member(Visibility.MEMBERS, Role.EDITOR, user)
        factories.get_site_with_member(Visibility.PUBLIC, Role.EDITOR, user)

        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 3

    @pytest.mark.django_db
    def test_language_admin_role(self):
        user = factories.UserFactory.create()
        factories.get_site_with_member(Visibility.TEAM, Role.LANGUAGE_ADMIN, user)
        factories.get_site_with_member(Visibility.MEMBERS, Role.LANGUAGE_ADMIN, user)
        factories.get_site_with_member(Visibility.PUBLIC, Role.LANGUAGE_ADMIN, user)

        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 3
