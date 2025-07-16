import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models import DictionaryEntry, Site
from backend.models.constants import AppRole, Visibility
from backend.tests.factories import get_app_admin


@pytest.mark.django_db(transaction=True)
class TestDataSearch:
    def setup_method(self):
        self.client = APIClient()
        self.admin_user = get_app_admin(AppRole.STAFF)
        self.site = Site(
            slug="sample",
            visibility=Visibility.PUBLIC,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.site.save()

    def test_exact_match(self):
        """
        Base case test to verify if the server is up and running.
        """

        # If there are any entries from previous tests
        DictionaryEntry.objects.filter(site=self.site).delete()

        entry_fish = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_fish.save()
        entry_mountain = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Mountain",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_mountain.save()
        entry_apple = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Apple",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_apple.save()

        url = reverse(
            "api:site-search-list", current_app="backend", args=[self.site.slug]
        )
        response = self.client.get(url + "?q=fish")
        assert response.status_code == 200

        response = response.json()
        assert response["count"] == 1
        assert response["results"][0]["entry"]["id"] == str(entry_fish.id)

        # Clean-up since transaction=True so all entries get stored in the db
        entry_fish.delete()
        entry_mountain.delete()
        entry_apple.delete()

    def test_substring_match(self):
        # If there are any entries from previous tests
        DictionaryEntry.objects.filter(site=self.site).delete()

        entry_fishing = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fishing",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_fishing.save()
        entry_fisherman = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fisherman",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_fisherman.save()
        entry_apple = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Apple",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_apple.save()

        url = reverse(
            "api:site-search-list", current_app="backend", args=[self.site.slug]
        )
        response = self.client.get(url + "?q=fish")
        assert response.status_code == 200

        response = response.json()
        assert response["count"] == 2

        response_id_list = [
            response["results"][0]["entry"]["id"],
            response["results"][1]["entry"]["id"],
        ]
        assert str(entry_fishing.id) in response_id_list
        assert str(entry_fisherman.id) in response_id_list

        # Clean-up since transaction=True so all entries get stored in the db
        entry_fishing.delete()
        entry_fisherman.delete()
        entry_apple.delete()

    def test_fuzzy_match(self):
        # If there are any entries from previous tests
        DictionaryEntry.objects.filter(site=self.site).delete()

        entry_fish = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_fish.save()
        entry_dish = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="dish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_dish.save()
        entry_apple = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Apple",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_apple.save()

        url = reverse(
            "api:site-search-list", current_app="backend", args=[self.site.slug]
        )
        response = self.client.get(url + "?q=fish")
        assert response.status_code == 200

        response = response.json()
        assert response["count"] == 2

        response_id_list = [
            response["results"][0]["entry"]["id"],
            response["results"][1]["entry"]["id"],
        ]
        assert str(entry_fish.id) in response_id_list
        assert str(entry_dish.id) in response_id_list

        # Clean-up since transaction=True so all entries get stored in the db
        entry_fish.delete()
        entry_dish.delete()
        entry_apple.delete()

    def test_relevance_order(self):
        # If there are any entries from previous tests
        DictionaryEntry.objects.filter(site=self.site).delete()

        entry_fish = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_fish.save()
        entry_fishing = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fishing",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_fishing.save()
        entry_dish = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Dish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_dish.save()

        url = reverse(
            "api:site-search-list", current_app="backend", args=[self.site.slug]
        )
        response = self.client.get(url + "?q=fish")
        assert response.status_code == 200

        response = response.json()
        assert response["count"] == 3

        results = [r["entry"]["title"] for r in response["results"]]

        assert results.index("Fish") < results.index("Fishing") < results.index("Dish")

        # Clean up
        entry_fish.delete()
        entry_fishing.delete()
        entry_dish.delete()
