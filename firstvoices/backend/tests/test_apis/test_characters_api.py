import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from .base_api_test import BaseSiteControlledContentApiTest


class TestCharactersEndpoints(BaseSiteControlledContentApiTest):
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:character-list"
    API_DETAIL_VIEW = "api:character-detail"
    CHARACTER_NOTE = "Test note"

    @pytest.mark.django_db
    def test_list_with_characters(self):
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

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 2
        assert response_data["count"] == 2

        character_json = response_data["results"][0]
        assert character_json == {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(character0.id))}",
            "id": str(character0.id),
            "title": "Ch0",
            "sortOrder": 1,
            "approximateForm": "Ch0",
            "notes": self.CHARACTER_NOTE,
            "variants": [],
            "relatedEntries": [],
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
        factories.CharacterVariantFactory.create(
            title="Ch0v0", base_character=character
        )

        variant_json = {
            "title": "Ch0v0",
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
            "sortOrder": 1,
            "approximateForm": "Ch0",
            "notes": self.CHARACTER_NOTE,
            "variants": [variant_json],
            "relatedEntries": [],
        }

    @pytest.mark.django_db
    def test_detail_variants(self):
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

        character1 = factories.CharacterFactory.create(
            title="Ch1", site=site, sort_order=2, approximate_form="Ch1", notes=""
        )

        variant = factories.CharacterVariantFactory.create(
            title="Ch0v0", base_character=character0
        )
        factories.CharacterVariantFactory.create(
            title="Ch0v1", base_character=character1
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(character0.id))
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["id"] == str(character0.id)
        assert len(response_data["variants"]) == 1
        assert response_data["variants"] == [
            {
                "title": variant.title,
            }
        ]

    @pytest.mark.django_db
    def test_detail_related_entries(self):
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

        entry1 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=entry1
        )
        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=entry2
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(character.id))
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["id"] == str(character.id)
        assert len(response_data["relatedEntries"]) == 1
        assert response_data["relatedEntries"] == [
            {
                "id": str(entry1.id),
                "title": entry1.title,
                "url": f"http://testserver/api/1.0/sites/{site.slug}/dictionary/{str(entry1.id)}/",
            }
        ]

    @pytest.mark.django_db
    def test_detail_404_site_not_found(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        factories.SiteFactory(visibility=Visibility.PUBLIC)
        character = factories.CharacterFactory.create()

        response = self.client.get(
            self.get_detail_endpoint(site_slug="invalid", key=character.id)
        )

        assert response.status_code == 404

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
