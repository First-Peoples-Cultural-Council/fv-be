import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models import DictionaryEntry, Site
from backend.models.constants import AppRole, Visibility
from backend.tests.factories import DictionaryEntryFactory, get_app_admin


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

    def teardown_method(self):
        DictionaryEntry.objects.filter(site=self.site).delete()

    def get_search_response(self, query):
        url = reverse(
            "api:site-search-list", current_app="backend", args=[self.site.slug]
        )
        response = self.client.get(f"{url}?q={query}")
        assert response.status_code == 200
        return response.json()

    def test_exact_match(self):
        """
        Base case test to verify if the server is up and running.
        """

        # If there are any entries from previous tests
        DictionaryEntry.objects.filter(site=self.site).delete()

        entry_fish = DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Mountain",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Apple",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )

        response = self.get_search_response("fish")
        assert response["count"] == 1
        assert response["results"][0]["entry"]["id"] == str(entry_fish.id)

    def test_substring_match(self):
        # If there are any entries from previous tests
        DictionaryEntry.objects.filter(site=self.site).delete()

        entry_fishing = DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fishing",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_fisherman = DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fisherman",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Apple",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )

        response = self.get_search_response("fish")
        assert response["count"] == 2

        response_id_list = [
            response["results"][0]["entry"]["id"],
            response["results"][1]["entry"]["id"],
        ]
        assert str(entry_fishing.id) in response_id_list
        assert str(entry_fisherman.id) in response_id_list

    def test_fuzzy_match(self):
        # If there are any entries from previous tests
        DictionaryEntry.objects.filter(site=self.site).delete()

        entry_fish = DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        entry_dish = DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="dish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Apple",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )

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

    def test_relevance_order(self):
        # If there are any entries from previous tests
        DictionaryEntry.objects.filter(site=self.site).delete()

        DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Fishing",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Dish",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )

        url = reverse(
            "api:site-search-list", current_app="backend", args=[self.site.slug]
        )
        response = self.client.get(url + "?q=fish")
        assert response.status_code == 200

        response = response.json()
        assert response["count"] == 3

        results = [r["entry"]["title"] for r in response["results"]]

        assert results.index("Fish") < results.index("Fishing") < results.index("Dish")
