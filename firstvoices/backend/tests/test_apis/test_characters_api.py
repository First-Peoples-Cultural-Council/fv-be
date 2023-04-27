import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from .base_api_test import BaseSiteContentApiTest


class TestCharactersEndpoints(BaseSiteContentApiTest):
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:characters-list"
    API_DETAIL_VIEW = "api:characters-detail"
    CHARACTER_NOTE = "Test note"

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
    def test_list_with_characters_and_variants(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

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

        factories.CharacterVariantFactory.create(
            title="Ch0v0", base_character=character0
        )
        factories.CharacterVariantFactory.create(
            title="Ch0v1", base_character=character0
        )

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 2
        assert response_data["count"] == 2

        character_json = response_data["results"][0]
        variant_json0 = character_json["variants"][0]
        variant_json1 = character_json["variants"][1]

        assert character_json == {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(character0.id))}",
            "id": str(character0.id),
            "title": "Ch0",
            "site": site.title,
            "sortOrder": 1,
            "approximateForm": "Ch0",
            "notes": self.CHARACTER_NOTE,
            "variants": [variant_json0, variant_json1],
        }
        assert variant_json0 == {
            "id": str(character0.variants.all()[0].id),
            "title": "Ch0v0",
            "baseCharacter": f"{character0.title} - {character0.site.title}",
        }
        assert variant_json1 == {
            "id": str(character0.variants.all()[1].id),
            "title": "Ch0v1",
            "baseCharacter": f"{character0.title} - {character0.site.title}",
        }

    # Test that users can only access characters if they have the correct role in a site
    @pytest.mark.django_db
    def test_list_permissions(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)
        factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            notes=self.CHARACTER_NOTE,
        )

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
        character = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            notes=self.CHARACTER_NOTE,
        )
        variant = factories.CharacterVariantFactory.create(
            title="Ch0v0", base_character=character
        )

        variant_json = {
            "id": str(variant.id),
            "title": "Ch0v0",
            "baseCharacter": f"{character.title} - {character.site.title}",
        }

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(character.id))
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(character.id))}",
            "id": str(character.id),
            "title": "Ch0",
            "site": site.title,
            "sortOrder": 1,
            "approximateForm": "Ch0",
            "notes": self.CHARACTER_NOTE,
            "variants": [variant_json],
        }

    @pytest.mark.django_db
    def test_detail_403(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)
        character = factories.CharacterFactory.create(title="Ch0", site=site)
        factories.CharacterVariantFactory.create(
            title="Ch0v0", base_character=character
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(character.id))
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_detail_404(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key="invalid")
        )

        assert response.status_code == 404

    # Test that users can only access character detail if they have the correct role in a site
    @pytest.mark.django_db
    def test_detail_permissions(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory(visibility=Visibility.TEAM)
        character = factories.CharacterFactory.create(title="Ch0", site=site)
        factories.CharacterVariantFactory.create(
            title="Ch0v0", base_character=character
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(character.id))
        )

        assert response.status_code == 403

        factories.MembershipFactory(user=user, site=site, role=Role.LANGUAGE_ADMIN)
        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(character.id))
        )

        assert response.status_code == 200
        assert json.loads(response.content)["id"] == str(character.id)
