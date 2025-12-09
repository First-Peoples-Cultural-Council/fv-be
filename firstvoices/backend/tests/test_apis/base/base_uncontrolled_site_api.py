import json

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlencode
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_api_test import WriteApiTestMixin


class BaseSiteContentApiTest:
    """
    Minimal setup for site content api integration testing.
    """

    APP_NAME = "backend"
    client = None

    def setup_method(self):
        self.client = APIClient()

    def create_site_with_non_member(self, site_visibility):
        site, _ = factories.get_site_with_authenticated_nonmember(
            self.client, visibility=site_visibility
        )
        return site

    def create_minimal_instance(self, site, visibility):
        raise NotImplementedError()

    def get_expected_response(self, instance, site):
        raise NotImplementedError()

    def get_lookup_key(self, instance):
        return instance.id


class SiteContentListEndpointMixin:
    API_LIST_VIEW = ""  # E.g., "api:site-list"

    def get_list_endpoint(self, site_slug, query_kwargs=None):
        """
        query_kwargs accept query parameters e.g. query_kwargs={"contains": "WORD"}
        """
        url = reverse(self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug])
        if query_kwargs:
            return f"{url}?{urlencode(query_kwargs)}"
        return url


class SiteContentListApiTestMixin(SiteContentListEndpointMixin):
    """
    For use with BaseSiteContentApiTest
    """

    def get_expected_list_response_item(self, instance, site):
        return self.get_expected_response(instance, site)

    def get_expected_list_response_item_no_email_access(self, instance, site):
        response_item = self.get_expected_list_response_item(instance, site)
        response_item.pop("createdBy", None)
        response_item.pop("lastModifiedBy", None)
        response_item.pop("systemLastModifiedBy", None)
        return response_item

    def assert_minimal_list_response(self, response, instance):
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance, instance.site
        )

    @pytest.mark.django_db
    def test_list_404_site_not_found(self):
        response = self.client.get(self.get_list_endpoint(site_slug="missing-site"))
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.django_db
    def test_list_403_when_site_not_visible(self, visibility):
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

    @pytest.mark.django_db
    def test_list_minimal(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        self.assert_minimal_list_response(response, instance)


class SiteContentListPermissionTestMixin:
    """Test cases for view permissions by site and content visibility. Use with SiteContentListApiTestMixin"""

    def assert_minimal_list_response_no_email_access(self, response, instance):
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 1

        assert response_data["results"][
            0
        ] == self.get_expected_list_response_item_no_email_access(
            instance, instance.site
        )

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access_success(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.MEMBERS, role=role
        )
        instance = self.create_minimal_instance(
            site=site, visibility=Visibility.MEMBERS
        )

        response = self.client.get(self.get_list_endpoint(site.slug))

        if role == Role.MEMBER:
            self.assert_minimal_list_response_no_email_access(response, instance)
        else:
            self.assert_minimal_list_response(response, instance)

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_list_nonpublic_access_denied_for_non_member(self, visibility):
        site, _ = factories.get_site_with_authenticated_nonmember(
            self.client, visibility=visibility
        )
        self.create_minimal_instance(site=site, visibility=visibility)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 403

    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_list_team_access_success(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.TEAM, role=role
        )
        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site.slug))
        self.assert_minimal_list_response(response, instance)

    @pytest.mark.django_db
    def test_list_team_access_denied_for_member(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.TEAM, role=Role.MEMBER
        )
        self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 403


class SiteContentDetailEndpointMixin:
    API_DETAIL_VIEW = ""  # E.g., "api:site-detail"

    def get_detail_endpoint(self, key, site_slug):
        return reverse(
            self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[site_slug, str(key)]
        )


class SiteContentDetailApiTestMixin(SiteContentDetailEndpointMixin):
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
            "systemLastModified": instance.system_last_modified.astimezone().isoformat(),
            "systemLastModifiedBy": instance.system_last_modified_by.email,
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
        }

    def get_expected_entry_standard_fields(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "title": instance.title,
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

    @pytest.mark.django_db
    def test_detail_minimal(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == self.get_expected_detail_response(instance, site)


class SiteContentDetailPermissionTestMixin:
    """Test cases for view permissions by site and content visibility."""

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_detail_member_access_success(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.MEMBERS, role=role
        )
        instance = self.create_minimal_instance(
            site=site, visibility=Visibility.MEMBERS
        )

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_detail_nonpublic_access_denied_for_non_member(self, visibility):
        site, _ = factories.get_site_with_authenticated_nonmember(
            self.client, visibility
        )
        instance = self.create_minimal_instance(site=site, visibility=visibility)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_detail_nonpublic_access_denied_for_guest(self, visibility):
        site = factories.SiteFactory.create(visibility=visibility)
        instance = self.create_minimal_instance(site=site, visibility=visibility)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_detail_team_access_success(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.TEAM, role=role
        )
        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_detail_team_access_denied_for_member(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.TEAM, role=Role.MEMBER
        )
        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403


class SiteContentCreateApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    @pytest.mark.django_db
    def test_create_invalid_400(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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

    @pytest.mark.django_db
    def test_create_confirm_user(self):
        site, user = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        response_data = json.loads(response.content)
        instance = self.model.objects.get(id=response_data["id"])

        assert instance.created_by.email == user.email
        assert instance.last_modified_by.email == user.email
        assert instance.system_last_modified_by.email == user.email

    @pytest.mark.django_db
    def test_create_with_nulls_success_201(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        data = self.get_valid_data_with_nulls(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

        response_data = json.loads(response.content)
        pk = response_data["id"]

        expected_data = self.add_expected_defaults(data)
        self.assert_created_instance(pk, expected_data)
        self.assert_created_response(expected_data, response_data)

    @pytest.mark.django_db
    def test_create_with_null_optional_charfields_success_201(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        data = self.get_valid_data_with_null_optional_charfields(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

        response_data = json.loads(response.content)
        pk = response_data["id"]

        expected_data = self.add_expected_defaults(data)
        self.assert_created_instance(pk, expected_data)
        self.assert_created_response(expected_data, response_data)

    def assert_created_instance(self, pk, data):
        raise NotImplementedError()

    def assert_created_response(self, expected_data, actual_response):
        raise NotImplementedError()


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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        response = self.client.put(
            self.get_detail_endpoint(key="missing-instance", site_slug=site.slug),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    def perform_successful_detail_request(self, instance, site, data):
        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )
        assert response.status_code == 200

        response_data = json.loads(response.content)
        return response_data

    def perform_successful_get_request_response(self, instance, site, detail=False):
        if detail:
            response = self.client.get(
                self.get_detail_endpoint(
                    key=self.get_lookup_key(instance), site_slug=site.slug
                )
            )
        else:
            response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        return response

    @pytest.mark.django_db
    def test_update_success_200(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        response_data = self.perform_successful_detail_request(instance, site, data)
        self.assert_updated_instance(data, self.get_updated_instance(instance))
        self.assert_update_response(data, response_data)

    @pytest.mark.django_db
    def test_update_confirm_user(self):
        site, user = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        self.perform_successful_detail_request(instance, site, data)

        updated_instance = self.get_updated_instance(instance)
        assert updated_instance.last_modified_by.email == user.email
        assert updated_instance.system_last_modified_by.email == user.email

    @pytest.mark.django_db
    def test_update_with_nulls_success_200(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data_with_nulls(site)
        expected_data = self.add_expected_defaults(data)

        response_data = self.perform_successful_detail_request(instance, site, data)
        self.assert_updated_instance(expected_data, self.get_updated_instance(instance))
        self.assert_update_response(expected_data, response_data)

    @pytest.mark.django_db
    def test_update_with_null_optional_charfields_success_200(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data_with_null_optional_charfields(site)
        expected_data = self.add_expected_defaults(data)

        response_data = self.perform_successful_detail_request(instance, site, data)
        self.assert_updated_instance(expected_data, self.get_updated_instance(instance))
        self.assert_update_response(expected_data, response_data)


class SiteContentDestroyApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    def add_related_objects(self, instance):
        raise NotImplementedError

    def assert_related_objects_deleted(self, instance):
        raise NotImplementedError

    def assert_instance_deleted(self, instance):
        if instance:
            with pytest.raises(ObjectDoesNotExist):
                type(instance).objects.get(id=instance.id)

    @pytest.mark.django_db
    def test_destroy_success_204(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        response = self.client.delete(
            self.get_detail_endpoint(key="missing-instance", site_slug=site.slug)
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_destroy_site_missing_404(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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

    def get_valid_patch_data(self, site):
        """Returns valid data object suitable for patch requests"""
        raise NotImplementedError()

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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        response = self.client.patch(
            self.get_detail_endpoint(key="missing-instance", site_slug=site.slug),
            data=self.format_upload_data(self.get_valid_patch_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_patch_success_200(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
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

    @pytest.mark.django_db
    def test_patch_confirm_user(self):
        site, user = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
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

        updated_instance = self.get_updated_patch_instance(instance)
        assert updated_instance.last_modified_by.email == user.email
        assert updated_instance.system_last_modified_by.email == user.email


class BaseReadOnlyUncontrolledSiteContentApiTest(
    SiteContentListApiTestMixin,
    SiteContentListPermissionTestMixin,
    SiteContentDetailApiTestMixin,
    SiteContentDetailPermissionTestMixin,
    BaseSiteContentApiTest,
):
    pass


class BaseUncontrolledSiteContentApiTest(
    WriteApiTestMixin,
    SiteContentCreateApiTestMixin,
    SiteContentUpdateApiTestMixin,
    SiteContentPatchApiTestMixin,
    SiteContentDestroyApiTestMixin,
    SiteContentListApiTestMixin,
    SiteContentListPermissionTestMixin,
    SiteContentDetailApiTestMixin,
    SiteContentDetailPermissionTestMixin,
    BaseSiteContentApiTest,
):
    pass
