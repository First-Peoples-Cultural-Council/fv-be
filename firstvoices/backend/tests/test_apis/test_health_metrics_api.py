import json

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentListApiTestMixin,
)


@pytest.mark.django_db
class TestHealthMetricsEndpoint(SiteContentListApiTestMixin, BaseSiteContentApiTest):
    API_LIST_VIEW = "api:health-metrics-list"

    @staticmethod
    def get_empty_health_metrics():
        return {
            "entries": {
                "entriesWithoutAudio": {"total": 0, "completionPercentage": 100},
                "entriesWithoutCategories": {"total": 0, "completionPercentage": 100},
                "entriesWithoutImages": {"total": 0, "completionPercentage": 100},
                "entriesWithoutRelatedEntries": {
                    "total": 0,
                    "completionPercentage": 100,
                },
                "entriesWithoutTranslations": {"total": 0, "completionPercentage": 100},
            },
            "characters": {
                "charactersWithoutAudio": {"total": 0, "completionPercentage": 100},
                "charactersWithoutImages": {"total": 0, "completionPercentage": 100},
                "charactersWithoutRelatedEntries": {
                    "total": 0,
                    "completionPercentage": 100,
                },
            },
        }

    def setup_dictionary_entries(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.LANGUAGE_ADMIN
        )
        factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryFactory.create(site=site)
        return site

    def setup_characters(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.LANGUAGE_ADMIN
        )
        factories.CharacterFactory.create(site=site)
        factories.CharacterFactory.create(site=site)
        return site

    @pytest.mark.skip(reason="Health metrics API does not create an instance")
    def test_list_minimal(self):
        # Health metrics API does not create a model instance
        pass

    def test_list_empty(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.ASSISTANT
        )
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == self.get_empty_health_metrics()

    def test_metrics_inaccessible_to_anonymous_users(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 401

    def test_metrics_inaccessible_to_non_members(self):
        site, user = factories.get_site_with_authenticated_nonmember(
            self.client, visibility=Visibility.PUBLIC
        )
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 403

    def test_metrics_inaccessible_to_members(self):
        site, user = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.MEMBER
        )
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 403

    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_metrics_accessible_to_language_admins(self, role):
        site, user = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=role
        )
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200

    @pytest.mark.parametrize("approle", [AppRole.STAFF, AppRole.SUPERADMIN])
    def test_metrics_accessible_to_staff(self, approle):
        site, user = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=approle
        )
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200

    def test_entries_without_audio(self):
        site = self.setup_dictionary_entries()
        audio = factories.AudioFactory.create(site=site)
        factories.DictionaryEntryFactory.create(site=site, related_audio=[audio])

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["entries"]["entriesWithoutAudio"]["total"] == 2
        assert (
            response_data["entries"]["entriesWithoutAudio"]["completionPercentage"]
            == 33
        )

    def test_entries_without_categories(self):
        site = self.setup_dictionary_entries()
        entry_with_category = factories.DictionaryEntryFactory.create(site=site)
        category = factories.CategoryFactory.create(site=site)
        entry_with_category.categories.add(category)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["entries"]["entriesWithoutCategories"]["total"] == 2
        assert (
            response_data["entries"]["entriesWithoutCategories"]["completionPercentage"]
            == 33
        )

    def test_entries_without_images(self):
        site = self.setup_dictionary_entries()
        image = factories.ImageFactory.create(site=site)
        factories.DictionaryEntryFactory.create(site=site, related_images=[image])

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["entries"]["entriesWithoutImages"]["total"] == 2
        assert (
            response_data["entries"]["entriesWithoutImages"]["completionPercentage"]
            == 33
        )

    def test_entries_without_related_entries(self):
        site = self.setup_dictionary_entries()
        related_entry = factories.DictionaryEntryFactory.create(site=site)
        related_entry2 = factories.DictionaryEntryFactory.create(site=site)

        factories.DictionaryEntryLinkFactory.create(
            from_dictionary_entry=related_entry, to_dictionary_entry=related_entry2
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["entries"]["entriesWithoutRelatedEntries"]["total"] == 3
        assert (
            response_data["entries"]["entriesWithoutRelatedEntries"][
                "completionPercentage"
            ]
            == 25
        )

    def test_entries_without_translations(self):
        site = self.setup_dictionary_entries()
        factories.DictionaryEntryFactory.create(site=site, translations=[])

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["entries"]["entriesWithoutTranslations"]["total"] == 1
        assert (
            response_data["entries"]["entriesWithoutTranslations"][
                "completionPercentage"
            ]
            == 67
        )

    def test_characters_without_audio(self):
        site = self.setup_characters()
        audio = factories.AudioFactory.create(site=site)
        factories.CharacterFactory.create(site=site, related_audio=[audio])

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["characters"]["charactersWithoutAudio"]["total"] == 2
        assert (
            response_data["characters"]["charactersWithoutAudio"][
                "completionPercentage"
            ]
            == 33
        )

    def test_characters_without_images(self):
        site = self.setup_characters()
        image = factories.ImageFactory.create(site=site)
        factories.CharacterFactory.create(site=site, related_images=[image])

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["characters"]["charactersWithoutImages"]["total"] == 2
        assert (
            response_data["characters"]["charactersWithoutImages"][
                "completionPercentage"
            ]
            == 33
        )

    def test_characters_without_related_entries(self):
        site = self.setup_characters()
        character = factories.CharacterFactory.create(site=site)
        related_entry = factories.DictionaryEntryFactory.create(site=site)

        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=related_entry
        )

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert (
            response_data["characters"]["charactersWithoutRelatedEntries"]["total"] == 2
        )
        assert (
            response_data["characters"]["charactersWithoutRelatedEntries"][
                "completionPercentage"
            ]
            == 33
        )
