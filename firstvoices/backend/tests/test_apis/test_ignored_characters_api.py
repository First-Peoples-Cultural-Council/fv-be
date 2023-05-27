from backend.tests import factories

from .base_api_test import BaseReadOnlyUncontrolledSiteContentApiTest


class TestIgnoredCharactersEndpoints(BaseReadOnlyUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:ignoredcharacter-list"
    API_DETAIL_VIEW = "api:ignoredcharacter-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.IgnoredCharacterFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(key=instance.id, site_slug=site.slug)}",
            "id": str(instance.id),
            "title": instance.title,
        }
