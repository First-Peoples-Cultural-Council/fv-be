from backend.models import JoinRequest
from backend.models.join_request import JoinRequestReason, JoinRequestStatus
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
)


class TestJoinRequestEndpoints(BaseReadOnlyUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the join request endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:join-request-list"
    API_DETAIL_VIEW = "api:join-request-detail"

    model = JoinRequest

    def create_minimal_instance(self, site, visibility=None):
        return factories.JoinRequestFactory(
            site=site,
            status=JoinRequestStatus.PENDING,
            reason=JoinRequestReason.OTHER,
            reason_note="Test reason note",
        )

    def get_expected_response(self, instance, site):
        return {
            "created": instance.created.astimezone().isoformat(),
            "createdBy": instance.created_by.email,
            "lastModified": instance.last_modified.astimezone().isoformat(),
            "lastModifiedBy": instance.last_modified_by.email,
            "id": str(instance.id),
            "url": f"http://testserver{self.get_detail_endpoint(instance.id, instance.site.slug)}",
            "site": {
                "id": str(site.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}",
                "title": site.title,
                "slug": site.slug,
                "visibility": instance.site.get_visibility_display().lower(),
                "language": site.language.title,
            },
            "user": {
                "id": int(instance.user.id),
                "email": instance.user.email,
                "firstName": instance.user.first_name,
                "lastName": instance.user.last_name,
            },
            "status": "Pending",
            "reason": "Other",
            "reasonNote": "Test reason note",
        }

    def get_expected_detail_response(self, instance, site):
        return self.get_expected_response(instance, site)
