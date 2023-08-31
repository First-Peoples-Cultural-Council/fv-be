import json

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlencode
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories


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

    def create_minimal_instance(self, visibility):
        raise NotImplementedError()

    def get_expected_response(self, instance):
        raise NotImplementedError()


class ListApiTestMixin:
    """
    Basic tests for non-site-content list APIs. Use with BaseApiTest.

    Does NOT include permission-related tests.
    """

    def get_expected_list_response_item(self, instance):
        return self.get_expected_response(instance)

    @pytest.mark.django_db
    def test_list_empty(self):
        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_list_minimal(self):
        instance = self.create_minimal_instance(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance
        )


class DetailApiTestMixin:
    """
    Basic tests for non-site-content detail APIs. Use with BaseApiTest.

    Does NOT include permission-related tests.
    """

    def get_expected_detail_response(self, instance):
        return self.get_expected_response(instance)

    @pytest.mark.django_db
    def test_detail_404(self):
        response = self.client.get(self.get_detail_endpoint("fake-key"))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detail_minimal(self):
        instance = self.create_minimal_instance(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=instance.id))

        assert response.status_code == 200

        response_data = json.loads(response.content)

        assert response_data == self.get_expected_detail_response(instance)


class ReadOnlyApiTests(ListApiTestMixin, DetailApiTestMixin, BaseApiTest):
    pass


class BaseSiteContentApiTest:
    """
    Minimal setup for site content api integration testing.
    """

    API_LIST_VIEW = ""  # E.g., "api:site-list"
    API_DETAIL_VIEW = ""  # E.g., "api:site-detail"
    APP_NAME = "backend"

    client = None

    def get_list_endpoint(self, site_slug, query_kwargs=None):
        """
        query_kwargs accept query parameters e.g. query_kwargs={"contains": "WORD"}
        """
        url = reverse(self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug])
        if query_kwargs:
            return f"{url}?{urlencode(query_kwargs)}"
        return url

    def get_detail_endpoint(self, key, site_slug):
        return reverse(
            self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[site_slug, str(key)]
        )

    def setup_method(self):
        self.client = APIClient()

    def create_site_with_non_member(self, site_visibility):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=site_visibility)

        return site

    def create_minimal_instance(self, site, visibility):
        raise NotImplementedError()

    def get_expected_response(self, instance, site):
        raise NotImplementedError()

    def get_lookup_key(self, instance):
        return instance.id


class SiteContentListApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    def get_expected_list_response_item(self, instance, site):
        return self.get_expected_response(instance, site)

    @pytest.mark.django_db
    def test_list_404_site_not_found(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site_slug="missing-site"))

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.django_db
    def test_list_403_site_not_visible(self, visibility):
        site = self.create_site_with_non_member(visibility)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_list_empty(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_minimal(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance, site
        )


class SiteContentDetailApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    def get_expected_detail_response(self, instance, site):
        return self.get_expected_response(instance, site)

    def get_expected_standard_fields(self, instance, site):
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

    @pytest.mark.django_db
    def test_detail_404_unknown_key(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        response = self.client.get(
            self.get_detail_endpoint(key="fake-key", site_slug=site.slug)
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detail_404_site_not_found(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug="invalid"
            )
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detail_403_site_not_visible(self):
        site = self.create_site_with_non_member(Visibility.MEMBERS)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_detail_member_access(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(
            site=site, visibility=Visibility.MEMBERS
        )

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_detail_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_detail_minimal(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == self.get_expected_detail_response(instance, site)


class ControlledListApiTestMixin:
    """
    For use with BaseSiteContentApiTest. Additional test cases for items with their own visibility settings, suitable
    for testing APIs related to BaseControlledSiteContentModel.
    """

    @pytest.mark.django_db
    def test_list_permissions(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        self.create_minimal_instance(site=site, visibility=Visibility.MEMBERS)
        self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance, site
        )


class ControlledDetailApiTestMixin:
    """
    For use with BaseSiteContentApiTest. Additional test cases for items with their own visibility settings, suitable
    for testing APIs related to BaseControlledSiteContentModel.
    """

    def get_expected_controlled_standard_fields(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "visibility": instance.get_visibility_display(),
        }

    @pytest.mark.django_db
    def test_detail_403_entry_not_visible(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403


class WriteApiTestMixin:
    """Common functions for Create and Update tests"""

    content_type = "application/json"

    def get_invalid_data(self):
        """Returns an invalid data object suitable for failing create/update requests"""
        return {}

    def get_valid_data(self, site=None):
        """Returns a valid data object suitable for create/update requests"""
        raise NotImplementedError

    def format_upload_data(self, data):
        """Subclasses can override this to support something other than json"""
        return json.dumps(data)

    def create_site_with_app_admin(self, site_visibility, role=AppRole.SUPERADMIN):
        user = factories.get_app_admin(role)
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=site_visibility)

        return site


class SiteContentCreateApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    @pytest.mark.django_db
    def test_create_invalid_400(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(self.get_invalid_data()),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_private_site_403(self):
        site = self.create_site_with_non_member(Visibility.MEMBERS)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_create_site_missing_404(self):
        site = self.create_site_with_non_member(Visibility.MEMBERS)

        response = self.client.post(
            self.get_list_endpoint(site_slug="missing-site"),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_create_success_201(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

        response_data = json.loads(response.content)
        pk = response_data["id"]

        self.assert_created_instance(pk, data)
        self.assert_created_response(data, response_data)

    def assert_created_instance(self, pk, data):
        raise NotImplementedError()

    def assert_created_response(self, expected_data, actual_response):
        raise NotImplementedError()


class ControlledSiteContentCreateApiTestMixin:
    """
    For use with ControlledBaseSiteContentApiTest
    """

    @pytest.mark.django_db
    def test_create_assistant_permissions_valid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["visibility"] = "team"

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

    @pytest.mark.django_db
    def test_create_assistant_permissions_invalid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["visibility"] = "public"

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403


class SiteContentUpdateApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    model = None

    def get_updated_instance(self, original_instance):
        return self.model.objects.filter(pk=original_instance.pk).first()

    def assert_updated_instance(self, expected_data, actual_instance):
        raise NotImplementedError()

    def assert_update_response(self, expected_data, actual_response):
        raise NotImplementedError()

    @pytest.mark.django_db
    def test_update_invalid_400(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(self.get_invalid_data()),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_update_403(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_update_site_missing_404(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug="missing-site"
            ),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_update_instance_missing_404(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        response = self.client.put(
            self.get_detail_endpoint(key="missing-instance", site_slug=site.slug),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_update_success_200(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(instance.id)

        self.assert_updated_instance(data, self.get_updated_instance(instance))
        self.assert_update_response(data, response_data)


class ControlledSiteContentUpdateApiTestMixin:
    """
    For use with ControlledBaseSiteContentApiTest
    """

    @pytest.mark.django_db
    def test_update_assistant_permissions_valid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["visibility"] = "team"

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_update_assistant_permissions_invalid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["visibility"] = "public"

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403


class SiteContentDestroyApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    def add_related_objects(self, instance):
        raise NotImplementedError

    def assert_related_objects_deleted(self, instance):
        raise NotImplementedError

    def assert_instance_deleted(self, instance):
        with pytest.raises(ObjectDoesNotExist):
            type(instance).objects.get(id=instance.id)

    @pytest.mark.django_db
    def test_destroy_success_204(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        self.add_related_objects(instance)

        response = self.client.delete(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 204
        assert response.content == b""  # 0 bytes
        self.assert_instance_deleted(instance)
        self.assert_related_objects_deleted(instance)

    @pytest.mark.django_db
    def test_destroy_denied_403(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.delete(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_destroy_missing_404(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        response = self.client.delete(
            self.get_detail_endpoint(key="missing-instance", site_slug=site.slug)
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_destroy_site_missing_404(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.delete(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug="missing-site"
            )
        )

        assert response.status_code == 404


class SiteContentPatchApiTestMixin:
    """
    For use with BaseSiteContentApiTest and WriteApiTestMixin
    """

    model = None

    def get_invalid_patch_data(self):
        """Returns an invalid data object suitable for failing patch requests"""
        return None

    def create_original_instance_for_patch(self, site):
        raise NotImplementedError()

    def get_updated_patch_instance(self, original_instance):
        return self.model.objects.filter(pk=original_instance.pk).first()

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        raise NotImplementedError()

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        raise NotImplementedError()

    def assert_update_patch_response(self, original_instance, data, actual_response):
        raise NotImplementedError()

    @pytest.mark.django_db
    def test_patch_invalid_400(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(self.get_invalid_patch_data()),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_patch_403(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(self.get_valid_patch_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_patch_site_missing_404(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug="missing-site"
            ),
            data=self.format_upload_data(self.get_valid_patch_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_patch_instance_missing_404(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        response = self.client.patch(
            self.get_detail_endpoint(key="missing-instance", site_slug=site.slug),
            data=self.format_upload_data(self.get_valid_patch_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_patch_success_200(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_original_instance_for_patch(site=site)
        data = self.get_valid_patch_data(site)

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(instance.id)

        self.assert_patch_instance_original_fields(
            instance, self.get_updated_patch_instance(instance)
        )
        self.assert_patch_instance_updated_fields(
            data, self.get_updated_patch_instance(instance)
        )
        self.assert_update_patch_response(instance, data, response_data)


class BaseReadOnlyUncontrolledSiteContentApiTest(
    SiteContentListApiTestMixin, SiteContentDetailApiTestMixin, BaseSiteContentApiTest
):
    pass


class BaseUncontrolledSiteContentApiTest(
    WriteApiTestMixin,
    SiteContentCreateApiTestMixin,
    SiteContentUpdateApiTestMixin,
    SiteContentPatchApiTestMixin,
    SiteContentDestroyApiTestMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    pass


class BaseReadOnlyControlledSiteContentApiTest(
    ControlledListApiTestMixin,
    ControlledDetailApiTestMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    pass


class BaseControlledLanguageAdminOnlySiteContentAPITest(
    ControlledListApiTestMixin,
    ControlledDetailApiTestMixin,
    BaseUncontrolledSiteContentApiTest,
):
    pass


class BaseControlledSiteContentApiTest(
    ControlledSiteContentCreateApiTestMixin,
    ControlledSiteContentUpdateApiTestMixin,
    BaseControlledLanguageAdminOnlySiteContentAPITest,
):
    pass
