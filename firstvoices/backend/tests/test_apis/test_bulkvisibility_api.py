import json

import pytest

from backend.models.constants import Visibility
from backend.models.jobs import BulkVisibilityJob
from backend.tests import factories

from .base_api_test import BaseReadOnlyUncontrolledSiteContentApiTest


class TestBulkVisibilityEndpoints(BaseReadOnlyUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the bulk visibility endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:bulk-visibility-list"
    API_DETAIL_VIEW = "api:bulk-visibility-detail"

    model = BulkVisibilityJob

    def create_minimal_instance(self, site, visibility):
        return factories.BulkVisibilityJobFactory(site=site)

    def get_expected_detail_response(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "status": instance.get_status_display().lower(),
            "taskId": instance.task_id,
            "message": instance.message,
            "fromVisibility": instance.get_from_visibility_display().lower(),
            "toVisibility": instance.get_to_visibility_display().lower(),
        }

    def get_expected_response(self, instance, site):
        return self.get_expected_detail_response(instance, site)

    @pytest.mark.skip(reason="Bulk visibility jobs can only be accessed by superusers.")
    def test_detail_member_access(self, role):
        # Bulk visibility jobs can only be accessed by superusers.
        pass

    @pytest.mark.skip(reason="Bulk visibility jobs can only be accessed by superusers.")
    def test_detail_team_access(self, role):
        # Bulk visibility jobs can only be accessed by superusers.
        pass

    @pytest.mark.django_db
    def test_list_minimal(self):
        site = factories.SiteFactory.create()
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance, site
        )

    @pytest.mark.django_db
    def test_detail_minimal(self):
        site = factories.SiteFactory.create()
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == self.get_expected_detail_response(instance, site)
