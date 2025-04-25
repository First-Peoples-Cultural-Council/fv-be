import json

import pytest

from backend.models.constants import Visibility
from backend.models.jobs import BulkVisibilityJob
from backend.tests import factories

from .base.base_async_api_test import (
    BaseAsyncSiteContentApiTest,
    SuperAdminAsyncJobPermissionsMixin,
)


class TestBulkVisibilityEndpoints(
    SuperAdminAsyncJobPermissionsMixin,
    BaseAsyncSiteContentApiTest,
):
    """
    End-to-end tests that the bulk visibility endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:bulk-visibility-list"
    API_DETAIL_VIEW = "api:bulk-visibility-detail"

    model = BulkVisibilityJob

    @pytest.fixture(scope="function")
    def mocked_bulk_change_visibility_async_func(self, mocker):
        self.mocked_func = mocker.patch(
            "backend.views.bulkvisibilityjob_views.bulk_change_visibility.apply_async"
        )

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

    def get_valid_data(self, site=None):
        return {
            "from_visibility": "public",
            "to_visibility": "members",
        }

    def assert_created_instance(self, pk, data):
        instance = BulkVisibilityJob.objects.get(pk=pk)
        assert (
            instance.from_visibility
            == Visibility[data["from_visibility"].upper()].value
        )
        assert instance.to_visibility == Visibility[data["to_visibility"].upper()].value

    def assert_created_response(self, expected_data, actual_response):
        assert actual_response["fromVisibility"] == expected_data["from_visibility"]
        assert actual_response["toVisibility"] == expected_data["to_visibility"]

    @pytest.mark.skip(reason="Bulk visibility jobs have no eligible nulls.")
    def test_create_with_nulls_success_201(self):
        # Bulk visibility jobs have no eligible nulls.
        pass

    @pytest.mark.skip(
        reason="Bulk visibility jobs have no eligible optional charfields."
    )
    def test_create_with_null_optional_charfields_success_201(self):
        #  Bulk visibility jobs have no eligible optional charfields.
        pass

    @pytest.mark.skip(
        reason="Bulk visibility jobs have no eligible optional charfields."
    )
    def test_update_with_null_optional_charfields_success_200(self):
        # Bulk visibility jobs have no eligible optional charfields..
        pass

    @pytest.mark.django_db
    def test_more_than_1_visibility_bad_request_400(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        data = {
            "from_visibility": "public",
            "to_visibility": "team",
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data=data, format="json"
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data == {
            "nonFieldErrors": [
                "The difference between 'from_visibility' and 'to_visibility' must be exactly 1 step."
            ]
        }

    @pytest.mark.django_db
    def test_same_visibility_bad_request_400(self):
        site = factories.SiteFactory.create()
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        data = {
            "from_visibility": "public",
            "to_visibility": "public",
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data=data, format="json"
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data == {
            "nonFieldErrors": [
                "'from_visibility' and 'to_visibility' must be different."
            ]
        }

    @pytest.mark.django_db
    def test_from_visibility_different_than_sites_bad_request_400(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        data = {
            "from_visibility": "team",
            "to_visibility": "members",
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data=data, format="json"
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data == {
            "nonFieldErrors": [
                "'from_visibility' must match the site visibility: public."
            ]
        }

    @pytest.mark.django_db
    def test_bulk_change_visibility_called(
        self, mocked_bulk_change_visibility_async_func
    ):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        data = {
            "from_visibility": "public",
            "to_visibility": "members",
        }

        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post(
                self.get_list_endpoint(site_slug=site.slug), data=data, format="json"
            )

        assert response.status_code == 201
        assert self.mocked_func.call_count == 1
