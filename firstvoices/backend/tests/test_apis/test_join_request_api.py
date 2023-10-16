from backend.models import JoinRequest
from backend.models.join_request import JoinRequestReason, JoinRequestStatus
from backend.tests import factories
from backend.tests.test_apis.base_api_test import BaseUncontrolledSiteContentApiTest


class TestJoinRequestEndpoints(BaseUncontrolledSiteContentApiTest):
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

    def get_valid_data(self, site=None):
        return {
            "user": factories.UserFactory().email,
            "status": "pending",
            "reason": "other",
            "reason_note": "Test reason note",
        }

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.status.get_status_display() == expected_data["status"]
        assert actual_instance.reason.get_reason_display() == expected_data["reason"]
        assert actual_instance.reason_note == expected_data["reason_note"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["status"] == expected_data["status"]
        assert actual_response["reason"] == expected_data["reason"]
        assert actual_response["reasonNote"] == expected_data["reason_note"]

    def assert_created_instance(self, pk, data):
        instance = JoinRequest.objects.get(pk=pk)
        assert instance.status.get_status_display() == data["status"]
        assert instance.reason.get_reason_display() == data["reason"]
        assert instance.reason_note == data["reason_note"]

    def assert_created_response(self, expected_data, actual_response):
        assert actual_response["status"] == expected_data["status"]
        assert actual_response["reason"] == expected_data["reason"]
        assert actual_response["reasonNote"] == expected_data["reason_note"]

    def create_original_instance_for_patch(self, site):
        return factories.JoinRequestFactory(
            site=site,
            user=factories.UserFactory(),
            status=JoinRequestStatus.PENDING,
            reason=JoinRequestReason.OTHER,
            reason_note="Test reason note",
        )

    def get_valid_patch_data(self, site=None):
        return {
            "status": JoinRequestStatus.APPROVED,
        }

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass
