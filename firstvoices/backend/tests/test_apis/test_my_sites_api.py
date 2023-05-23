import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import BaseApiTest


class TestMySitesEndpoint(BaseApiTest):
    """
    End to end tests that check the my-sites endpoint for expected behavior.
    """

    API_LIST_VIEW = "api:my-sites-list"
    APP_NAME = "backend"

    @pytest.mark.django_db
    def test_list_empty(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 0

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
        assert len(response_data) == 0

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
        assert len(response_data) == 2
        assert response_data[0]["visibility"] == Visibility.MEMBERS.label
        assert response_data[1]["visibility"] == Visibility.PUBLIC.label

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
        assert len(response_data) == 3

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
        assert len(response_data) == 3

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
        assert len(response_data) == 3
