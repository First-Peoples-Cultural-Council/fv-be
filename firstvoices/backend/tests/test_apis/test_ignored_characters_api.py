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
            "created": instance.created.astimezone().isoformat(),
            "createdBy": instance.created_by.email,
            "lastModified": instance.last_modified.astimezone().isoformat(),
            "lastModifiedBy": instance.last_modified_by.email,
            "id": str(instance.id),
            "url": f"http://testserver{self.get_detail_endpoint(instance.id, instance.site.slug)}",
            "title": instance.title,
            "site": {
                "id": str(site.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}",
                "title": site.title,
                "slug": site.slug,
                "visibility": instance.site.get_visibility_display(),
                "language": site.language.title,
            },
        }
