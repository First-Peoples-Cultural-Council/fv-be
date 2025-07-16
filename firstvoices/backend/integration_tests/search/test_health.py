import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models import DictionaryEntry, Site
from backend.models.constants import AppRole, Visibility
from backend.tests.factories import get_app_admin


class TestESClusterHealth:
    @pytest.mark.django_db(transaction=True)
    def test_cluster_running(self):
        """
        Base case test to verify if the server is up and running.
        """

        client = APIClient()
        admin_user = get_app_admin(AppRole.STAFF)
        site = Site(
            slug="sample",
            visibility=Visibility.PUBLIC,
            created_by=admin_user,
            last_modified_by=admin_user,
        )
        site.save()
        sample_entry = DictionaryEntry(
            site=site,
            visibility=Visibility.PUBLIC,
            title="Sample entry",
            created_by=admin_user,
            last_modified_by=admin_user,
        )
        sample_entry.save()

        url = reverse("api:site-search-list", current_app="backend", args=[site.slug])
        response = client.get(url)
        assert response.status_code == 200

        response = response.json()
        assert response["count"] == 1
        assert response["results"][0]["entry"]["id"] == str(sample_entry.id)

        # Clean-up since transaction=True so all entries get stored in the db
        sample_entry.delete()
        site.delete()
