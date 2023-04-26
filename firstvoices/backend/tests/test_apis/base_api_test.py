from rest_framework.reverse import reverse
from rest_framework.test import APIClient


class BaseApiTest:
    """
    Minimal setup for api integration testing.
    """

    API_LIST_VIEW = ""  # E.g., "api:site-list"
    API_DETAIL_VIEW = ""  # E.g., "api:site-detail"
    APP_NAME = "backend"

    client = None

    def get_list_endpoint(self):
        return reverse(self.API_LIST_VIEW, current_app=self.APP_NAME)

    def get_detail_endpoint(self, key):
        return reverse(self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[key])

    def setup_method(self):
        self.client = APIClient()


class BaseSiteContentApiTest:
    """
    Minimal setup for site content api integration testing.
    """

    API_LIST_VIEW = ""  # E.g., "api:site-list"
    API_DETAIL_VIEW = ""  # E.g., "api:site-detail"
    APP_NAME = "backend"

    client = None

    def get_list_endpoint(self, site_slug):
        return reverse(self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug])

    def get_detail_endpoint(self, site_slug, key):
        return reverse(
            self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[site_slug, key]
        )

    def setup_method(self):
        self.client = APIClient()
