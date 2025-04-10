import pytest

from backend.models.constants import AppRole, Visibility
from backend.models.sites import SiteFeature
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseUncontrolledSiteContentApiTest,
)


class TestSiteFeatureEndpoints(BaseUncontrolledSiteContentApiTest):
    """
    End-to-end tests that check the site feature endpoint for expected behavior.
    """

    API_LIST_VIEW = "api:sitefeature-list"
    API_DETAIL_VIEW = "api:sitefeature-detail"
    TEST_KEY = "test"

    model = SiteFeature

    @pytest.fixture(scope="function", autouse=True)
    def mocked_media_async_func(self, mocker):
        self.mocked_func = mocker.patch(
            "backend.views.site_feature_views.request_sync_all_media_site_content_in_indexes"
        )

    def get_lookup_key(self, instance):
        return instance.key

    def create_minimal_instance(self, site, visibility):
        return factories.SiteFeatureFactory.create(site=site)

    def get_expected_detail_response(self, instance, site):
        return {
            "created": instance.created.astimezone().isoformat(),
            "createdBy": instance.created_by.email,
            "lastModified": instance.last_modified.astimezone().isoformat(),
            "lastModifiedBy": instance.last_modified_by.email,
            "id": str(instance.id),
            "url": f"http://testserver{self.get_detail_endpoint(instance.key, instance.site.slug)}",
            "site": {
                "id": str(site.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}",
                "title": site.title,
                "slug": site.slug,
                "visibility": instance.site.get_visibility_display().lower(),
                "language": site.language.title,
            },
            "key": instance.key,
            "isEnabled": instance.is_enabled,
        }

    def get_expected_response(self, instance, site):
        return self.get_expected_detail_response(instance, site)

    def get_valid_data(self, site=None):
        return {
            "key": self.TEST_KEY,
            "isEnabled": True,
        }

    def get_valid_patch_data(self, site=None):
        return {
            "isEnabled": False,
        }

    def add_expected_defaults(self, data):
        return data

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.is_enabled == expected_data["isEnabled"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["isEnabled"] == expected_data["isEnabled"]

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        assert instance.key == data["key"]
        assert instance.is_enabled == data["isEnabled"]

    def assert_created_response(self, expected_data, actual_response):
        assert actual_response["key"] == expected_data["key"]
        assert actual_response["isEnabled"] == expected_data["isEnabled"]

    def create_original_instance_for_patch(self, site):
        return self.create_minimal_instance(site, Visibility.PUBLIC)

    def add_related_objects(self, instance):
        # No related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # No related objects to delete
        pass

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        assert original_instance.key == updated_instance.key

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        assert updated_instance.is_enabled == data["isEnabled"]

    def assert_patch_response_original_fields(
        self, original_response, updated_response
    ):
        assert original_response["key"] == updated_response["key"]

    def assert_patch_response_updated_fields(self, data, updated_response):
        assert updated_response["isEnabled"] == data["isEnabled"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["key"] == original_instance.key
        assert actual_response["isEnabled"] == data["isEnabled"]

    @pytest.mark.skip(reason="SiteFeature API does not have eligible null fields.")
    def test_create_with_nulls_success_201(self):
        # SiteFeature API does not have eligible null fields.
        pass

    @pytest.mark.skip(reason="SiteFeature API does not have eligible null fields.")
    def test_update_with_nulls_success_200(self):
        # SiteFeature API does not have eligible null fields.
        pass

    @pytest.mark.skip(
        reason="SiteFeature API does not have eligible optional charfields."
    )
    def test_create_with_null_optional_charfields_success_201(self):
        # SiteFeature API does not have eligible optional charfields.
        pass

    @pytest.mark.skip(
        reason="SiteFeature API does not have eligible optional charfields."
    )
    def test_update_with_null_optional_charfields_success_200(self):
        # SiteFeature API does not have eligible optional charfields.
        pass

    @pytest.mark.django_db
    def test_feature_key_read_only(self):
        """
        Test that the feature key is read only after creation.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        feature = factories.SiteFeatureFactory.create(site=site)

        data = {
            "key": "new_key",
            "isEnabled": True,
        }

        response = self.client.put(
            self.get_detail_endpoint(key=feature.key, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["key"] == feature.key

    @pytest.mark.django_db
    def test_duplicate_key_validation(self):
        """
        Test that duplicate keys are not allowed.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        feature = factories.SiteFeatureFactory.create(site=site)

        data = {
            "key": feature.key,
            "isEnabled": True,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_site_feature_keys_only_unique_per_site(self):
        """
        Test that the site feature keys are unique per site, but the same key can be used in multiple sites.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        site2 = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        data = {
            "key": self.TEST_KEY,
            "is_enabled": True,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 201

        data = {
            "key": self.TEST_KEY,
            "is_enabled": True,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site2.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 201

    @pytest.mark.django_db
    def test_api_create_triggers_media_sync(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        self.client.force_authenticate(user=factories.get_app_admin(AppRole.SUPERADMIN))

        data = {
            "key": self.TEST_KEY,
            "isEnabled": True,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 201
        assert self.mocked_func.call_count == 1

    @pytest.mark.django_db
    def test_api_update_triggers_media_sync(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        feature = factories.SiteFeatureFactory.create(site=site)
        self.client.force_authenticate(user=factories.get_app_admin(AppRole.SUPERADMIN))

        data = {
            "key": feature.key,
            "isEnabled": False,
        }

        response = self.client.put(
            self.get_detail_endpoint(key=feature.key, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200
        assert self.mocked_func.call_count == 1

    @pytest.mark.django_db
    def test_api_delete_triggers_media_sync(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        feature = factories.SiteFeatureFactory.create(site=site)
        self.client.force_authenticate(user=factories.get_app_admin(AppRole.SUPERADMIN))

        response = self.client.delete(
            self.get_detail_endpoint(key=feature.key, site_slug=site.slug),
            format="json",
        )

        assert response.status_code == 204
        assert self.mocked_func.call_count == 1

    @pytest.mark.django_db
    def test_api_patch_triggers_media_sync(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        feature = factories.SiteFeatureFactory.create(site=site)
        self.client.force_authenticate(user=factories.get_app_admin(AppRole.SUPERADMIN))

        data = {
            "isEnabled": False,
        }

        response = self.client.patch(
            self.get_detail_endpoint(key=feature.key, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200
        assert self.mocked_func.call_count == 1
