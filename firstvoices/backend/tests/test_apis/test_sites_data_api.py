import pytest
from mothertongues.config.models import LanguageConfiguration
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Visibility
from backend.tests import factories


class TestSitesDataEndpoint:
    """
    Tests that check the sites-data endpoint for correct formatting and behavior.
    """

    API_MTD_VIEW = "api:mtd-data-list"
    APP_NAME = "backend"

    client = None

    def get_mtd_endpoint(self, site_slug):
        return reverse(self.API_MTD_VIEW, current_app=self.APP_NAME, args=[site_slug])

    def setup_method(self):
        self.client = APIClient()
        self.user = factories.get_non_member_user()
        self.client.force_authenticate(user=self.user)
        self.basic_config = LanguageConfiguration()

    @pytest.mark.django_db
    def test_no_build_and_score(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        response = self.client.get(self.get_mtd_endpoint(site_slug=site.slug))
        assert response.status_code == 404
