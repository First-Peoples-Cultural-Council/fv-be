from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
)


class TestIgnoredCharactersEndpoints(BaseReadOnlyUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:ignoredcharacter-list"
    API_DETAIL_VIEW = "api:ignoredcharacter-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.IgnoredCharacterFactory.create(site=site)

    def get_expected_response(self, instance, site):
        standard_fields = self.get_expected_entry_standard_fields(instance, site)
        return {
            **standard_fields,
        }
