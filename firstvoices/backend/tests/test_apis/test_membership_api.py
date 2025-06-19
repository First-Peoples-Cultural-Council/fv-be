import json

import pytest

from backend.models import Membership
from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SiteContentDestroyApiTestMixin,
    SiteContentDetailApiTestMixin,
    SiteContentListApiTestMixin,
    SiteContentPatchApiTestMixin,
    SiteContentUpdateApiTestMixin,
    WriteApiTestMixin,
)


class TestMembershipEndpoints(
    BaseSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SiteContentDestroyApiTestMixin,
    SiteContentDetailApiTestMixin,
    SiteContentListApiTestMixin,
    SiteContentPatchApiTestMixin,
    SiteContentUpdateApiTestMixin,
    WriteApiTestMixin,
):
    """
    End-to-end tests that the join request endpoints have the expected behaviour. Includes custom permission tests.
    """

    API_LIST_VIEW = "api:membership-list"
    API_DETAIL_VIEW = "api:membership-detail"

    model = Membership
    model_factory = factories.Membership

    def create_minimal_instance(self, site, role=Role.MEMBER, visibility=None):
        membership = factories.MembershipFactory(
            site=site,
            role=role,
        )
        return membership

    def get_expected_response(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "user": {
                "id": int(instance.user.id),
                "email": instance.user.email,
                "firstName": instance.user.first_name,
                "lastName": instance.user.last_name,
            },
            "role": instance.get_role_display(),
        }

    def get_expected_detail_response(self, instance, site):
        return self.get_expected_response(instance, site)

    def get_valid_data(self, site=None):
        user = factories.get_non_member_user()
        return {
            "role": "Assistant",
            "user_id": str(user.id),
        }

    def add_expected_defaults(self, data):
        return data

    def assert_created_instance(self, pk, data):
        instance = Membership.objects.get(pk=pk)
        assert instance.get_role_display() == data["role"]

    def assert_created_response(self, expected_data, actual_response):
        self.assert_update_response(expected_data, actual_response)

    def assert_updated_instance(self, expected_data, actual_instance):
        assert str(actual_instance.user.id) == expected_data["user_id"]
        assert actual_instance.get_role_display() == expected_data["role"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["role"] == expected_data["role"]

    def create_original_instance_for_patch(self, site):
        return factories.MembershipFactory(
            site=site,
            role=Role.MEMBER,
        )

    def get_valid_patch_data(self, site=None):
        return {"role": "Editor"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.user.id == original_instance.user.id

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        assert updated_instance.get_role_display() == data["role"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["role"] == data["role"]
        assert actual_response["user"]["id"] == original_instance.user.id

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass

    def test_create_with_null_optional_charfields_success_201(self):
        # Membership API does not have eligible optional charfields.
        pass

    def test_create_with_nulls_success_201(self):
        # Membership API does not have eligible optional fields.
        pass

    def test_update_with_null_optional_charfields_success_200(self):
        # Membership API does not have eligible optional charfields.
        pass

    def test_update_with_nulls_success_200(self):
        # Membership API does not have eligible optional fields.
        pass

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_detail_403_for_non_admins(self, role, visibility):
        site = factories.SiteFactory.create(visibility=visibility)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_detail_language_admin_access(self, visibility):
        site, admin = factories.get_site_with_member(visibility, Role.LANGUAGE_ADMIN)

        self.client.force_authenticate(user=admin)

        instance = self.create_minimal_instance(site=site)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    def get_list_response_data(self, site, user):
        #  Create three additional memberships for the site
        self.create_minimal_instance(site=site)
        self.create_minimal_instance(site=site)
        self.create_minimal_instance(site=site)

        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

        return json.loads(response.content)

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_list_for_non_admins(self, role):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=role
        )

        response_data = self.get_list_response_data(site, user)

        # List should only show memberships for current user if not Language Admin
        # Check if the list includes any memberships for other users
        has_access = any(
            membership["user"]["email"] != user.email
            for membership in response_data["results"]
        )
        assert has_access is False

    @pytest.mark.django_db
    def test_list_for_guest(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()

        response_data = self.get_list_response_data(site, user)
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_list_for_anon(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_anonymous_user()

        response_data = self.get_list_response_data(site, user)
        assert response_data["count"] == 0

    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_list_language_admin_access(self, visibility):
        site, admin = factories.get_site_with_member(visibility, Role.LANGUAGE_ADMIN)

        response_data = self.get_list_response_data(site=site, user=admin)

        #  Assert the membership total for the site including LA
        assert response_data["count"] == 4

    @pytest.mark.django_db
    def test_membership_unique_validation(self):
        """
        Test that a membership cannot be created for the same user and site.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory()
        factories.MembershipFactory(site=site, user=user)

        data = {
            "user_id": user.id,
            "role": "Editor",
        }
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400
