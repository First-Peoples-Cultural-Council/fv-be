import json

import pytest
from rest_framework.test import APIClient

from firstvoices.backend.models.constants import Role, Visibility
from firstvoices.backend.tests import factories


class TestCharactersEndpoints:
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    CHARACTER_NOTE = "This is a test character note"
    TEST_SITE_TITLE = "Test Site"

    endpoint = "/api/2.0/characters/"

    def setup_method(self):
        self.client = APIClient()

    # Test Empty character list
    @pytest.mark.django_db
    def test_list_empty(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 0

    # Test list with one site
    @pytest.mark.django_db
    def test_list_with_characters(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(
            title=self.TEST_SITE_TITLE, visibility=Visibility.PUBLIC
        )
        character0 = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            notes=self.CHARACTER_NOTE,
        )
        factories.CharacterFactory.create(
            title="Ch1", site=site, sort_order=2, approximate_form="Ch1", notes=""
        )

        response = self.client.get(self.endpoint)

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data) == 1

        assert response_data[0]["site"] == self.TEST_SITE_TITLE
        assert len(response_data[0]["characters"]) == 2

        character_json = response_data[0]["characters"][0]
        assert character_json == {
            "id": str(character0.id),
            "title": "Ch0",
            "site": site.title,
            "sortOrder": 1,
            "approximateForm": "Ch0",
            "notes": self.CHARACTER_NOTE,
        }

    # Test list with multiple sites and multiple characters
    @pytest.mark.django_db
    def test_list_with_multiple_characters_and_sites(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(
            title=self.TEST_SITE_TITLE, visibility=Visibility.PUBLIC
        )
        site2 = factories.SiteFactory(title="Test Site 2", visibility=Visibility.PUBLIC)
        character0 = factories.CharacterFactory.create(site=site, sort_order=1)
        factories.CharacterFactory.create(site=site, sort_order=2)
        character2 = factories.CharacterFactory.create(site=site2, sort_order=1)
        factories.CharacterFactory.create(site=site2, sort_order=2)

        response = self.client.get(self.endpoint)

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data) == 2

        assert response_data[0]["site"] == self.TEST_SITE_TITLE
        assert len(response_data[0]["characters"]) == 2

        assert response_data[1]["site"] == "Test Site 2"
        assert len(response_data[1]["characters"]) == 2

        character_json = response_data[0]["characters"][0]
        assert character_json["id"] == str(character0.id)

        character_json = response_data[1]["characters"][0]
        assert character_json["id"] == str(character2.id)

    # Test List Permissions
    @pytest.mark.django_db
    def test_list_permissions(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(
            title=self.TEST_SITE_TITLE, visibility=Visibility.TEAM
        )
        factories.CharacterFactory.create(site=site, sort_order=1)

        response = self.client.get(self.endpoint)

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data) == 0

    # Test detail
    @pytest.mark.django_db
    def test_detail(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(
            title=self.TEST_SITE_TITLE, visibility=Visibility.PUBLIC
        )
        character = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            notes=self.CHARACTER_NOTE,
        )

        response = self.client.get(f"{self.endpoint}{character.id}/")

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == {
            "id": str(character.id),
            "title": "Ch0",
            "site": site.title,
            "sortOrder": 1,
            "approximateForm": "Ch0",
            "notes": self.CHARACTER_NOTE,
        }

    # Test detail 403
    @pytest.mark.django_db
    def test_detail_403(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(
            title=self.TEST_SITE_TITLE, visibility=Visibility.TEAM
        )
        character = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            notes=self.CHARACTER_NOTE,
        )

        response = self.client.get(f"{self.endpoint}{character.id}/")

        assert response.status_code == 403

    # Test detail 404
    @pytest.mark.django_db
    def test_detail_404(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(f"{self.endpoint}1/")

        assert response.status_code == 404

    # Test that users can only access characters if they have the correct role in a site
    @pytest.mark.django_db
    def test_permissions(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(
            title=self.TEST_SITE_TITLE, visibility=Visibility.TEAM
        )
        character = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            notes=self.CHARACTER_NOTE,
        )

        response = self.client.get(f"{self.endpoint}{character.id}/")

        assert response.status_code == 403

        factories.MembershipFactory(user=user, site=site, role=Role.LANGUAGE_ADMIN)
        response = self.client.get(f"{self.endpoint}{character.id}/")

        assert response.status_code == 200
