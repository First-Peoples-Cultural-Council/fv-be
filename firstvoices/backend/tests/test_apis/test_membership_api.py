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
    End-to-end tests that the Membership endpoints have the expected behaviour. Includes custom permission tests.
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
            "user": user.email,
        }

    def add_expected_defaults(self, data):
        return data

    def assert_created_instance(self, pk, data):
        instance = Membership.objects.get(pk=pk)
        assert instance.user.email == data["user"]
        assert instance.get_role_display() == data["role"]

    def assert_created_response(self, expected_data, actual_response):
        assert actual_response["user"]["email"] == expected_data["user"]
        assert actual_response["role"] == expected_data["role"]

    def assert_updated_instance(self, expected_data, actual_instance):
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
        assert actual_response["user"]["email"] == original_instance.user.email

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
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=visibility, role=role
        )
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
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility, Role.LANGUAGE_ADMIN
        )
        instance = self.create_minimal_instance(site=site)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    def get_list_response_data(self, site):
        #  Create three additional memberships for the site
        self.create_minimal_instance(site=site)
        self.create_minimal_instance(site=site)
        self.create_minimal_instance(site=site)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

        return json.loads(response.content)

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_list_for_non_admins(self, role):
        site, user = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )

        response_data = self.get_list_response_data(site)

        # List should only show memberships for current user if not Language Admin
        # Check if the list includes any memberships for other users
        has_access = any(
            membership["user"]["email"] != user.email
            for membership in response_data["results"]
        )
        assert has_access is False

    @pytest.mark.django_db
    def test_list_for_guest(self):
        site, _ = factories.get_site_with_authenticated_nonmember(
            self.client, Visibility.PUBLIC
        )

        response_data = self.get_list_response_data(site)
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_list_for_anon(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_anonymous_user()
        self.client.force_authenticate(user=user)

        response_data = self.get_list_response_data(site)
        assert response_data["count"] == 0

    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_list_language_admin_access(self, visibility):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility, Role.LANGUAGE_ADMIN
        )

        response_data = self.get_list_response_data(site=site)

        #  Assert the membership total for the site including LA
        assert response_data["count"] == 4

    @pytest.mark.django_db
    def test_create_400_already_member(self):
        """
        Test that a membership cannot be created for the same user and site.
        """
        site, _ = factories.get_site_with_app_admin(
            self.client, Visibility.PUBLIC, AppRole.SUPERADMIN
        )
        instance = factories.MembershipFactory(site=site)

        data = {
            "user": instance.user.email,
            "role": "Editor",
        }
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_400_missing_user(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        data = {"role": "Editor"}

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_400_missing_role(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        user = factories.get_non_member_user()

        data = {"user": user.email}

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_400_invalid_role(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        user = factories.get_non_member_user()

        data = {
            "user": user.email,
            "role": "diva",
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_400_invalid_user(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

        data = {
            "user": "marge@email.com",
            "role": "Editor",
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_create_403_not_app_admin(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )

        data = self.get_valid_data()

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("app_role", [AppRole.STAFF, AppRole.SUPERADMIN])
    @pytest.mark.django_db
    def test_create_success_app_admin(self, app_role):
        site, _ = factories.get_site_with_app_admin(
            self.client, Visibility.PUBLIC, app_role
        )

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            format="json",
            data=self.get_valid_data(),
        )

        assert response.status_code == 201

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_update_403_not_admin(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )
        instance = factories.MembershipFactory.create(site=site)

        data = {
            "role": "Editor",
            "user": instance.user.email,
        }

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            format="json",
            data=data,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_update_success_admin(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        instance = factories.MembershipFactory.create(site=site)

        data = {
            "role": "Editor",
            "user": instance.user.email,
        }

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            format="json",
            data=data,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        self.assert_updated_instance(data, self.get_updated_instance(instance))
        self.assert_update_response(data, response_data)

    @pytest.mark.django_db
    def test_update_user_ignored(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        instance = factories.MembershipFactory.create(site=site)
        user_2 = factories.get_non_member_user()

        data = {
            "role": "Editor",
            "user": user_2.email,
        }

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)

        assert response_data["user"]["email"] != user_2.email
        assert response_data["user"]["email"] == instance.user.email

    @pytest.mark.django_db
    def test_update_403_admin_on_admin(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )

        # create a second language admin for the same site
        admin_membership_instance = factories.MembershipFactory.create(
            site=site, role=Role.LANGUAGE_ADMIN
        )

        data = {
            "role": "Editor",
            "user": admin_membership_instance.user.email,
        }

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(admin_membership_instance), site_slug=site.slug
            ),
            format="json",
            data=data,
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("app_role", [AppRole.STAFF, AppRole.SUPERADMIN])
    @pytest.mark.django_db
    def test_update_success_app_admin(self, app_role):
        site, _ = factories.get_site_with_app_admin(
            self.client, Visibility.PUBLIC, app_role
        )
        instance = factories.MembershipFactory.create(site=site)

        data = {
            "role": "Editor",
            "user": instance.user.email,
        }

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)

        self.assert_updated_instance(data, self.get_updated_instance(instance))
        self.assert_update_response(data, response_data)

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_patch_403_not_admin(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )
        user_2 = factories.get_non_member_user()
        instance = factories.MembershipFactory.create(user=user_2, site=site)

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            format="json",
            data=self.get_valid_patch_data(),
        )

        assert response.status_code == 403

    @pytest.mark.parametrize(
        "role_from,role_to",
        [
            (Role.MEMBER, Role.ASSISTANT),
            (Role.ASSISTANT, Role.EDITOR),
            (Role.EDITOR, Role.LANGUAGE_ADMIN),
        ],
    )
    @pytest.mark.django_db
    def test_patch_success_admin(self, role_from, role_to):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        instance = factories.MembershipFactory.create(site=site, role=role_from)

        data = {"role": role_to.label}

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        updated_instance = self.get_updated_instance(instance)

        self.assert_patch_instance_original_fields(instance, updated_instance)
        self.assert_patch_instance_updated_fields(data, updated_instance)

    @pytest.mark.django_db
    def test_patch_user_ignored(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        instance = factories.MembershipFactory.create(site=site)
        user_2 = factories.get_non_member_user()

        data = {"user": user_2.email}

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)

        assert response_data["user"]["email"] != user_2.email
        assert response_data["user"]["email"] == instance.user.email

    @pytest.mark.django_db
    def test_patch_403_admin_on_admin(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )

        # create a second language admin for the same site
        admin_membership_instance = factories.MembershipFactory.create(
            site=site, role=Role.LANGUAGE_ADMIN
        )

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(admin_membership_instance), site_slug=site.slug
            ),
            format="json",
            data=self.get_valid_patch_data(),
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("app_role", [AppRole.STAFF, AppRole.SUPERADMIN])
    @pytest.mark.parametrize(
        "role_from,role_to",
        [
            (Role.MEMBER, Role.ASSISTANT),
            (Role.ASSISTANT, Role.EDITOR),
            (Role.EDITOR, Role.LANGUAGE_ADMIN),
            (Role.LANGUAGE_ADMIN, Role.EDITOR),
        ],
    )
    @pytest.mark.django_db
    def test_patch_success_app_admin(self, app_role, role_from, role_to):
        site, _ = factories.get_site_with_app_admin(
            self.client, Visibility.PUBLIC, app_role
        )
        instance = factories.MembershipFactory.create(site=site, role=role_from)

        data = {"role": role_to.label}

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            format="json",
            data=data,
        )

        assert response.status_code == 200

        updated_instance = self.get_updated_instance(instance)

        self.assert_patch_instance_original_fields(instance, updated_instance)
        self.assert_patch_instance_updated_fields(data, updated_instance)

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_delete_403_not_admin(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )
        instance = factories.MembershipFactory.create(site=site)

        response = self.client.delete(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_delete_success_admin(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        instance = factories.MembershipFactory.create(site=site, role=role)

        response = self.client.delete(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
        )

        assert response.status_code == 204

    @pytest.mark.django_db
    def test_delete_403_admin_on_admin(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )

        # create a second language admin for the same site
        admin_membership_instance = factories.MembershipFactory.create(
            site=site, role=Role.LANGUAGE_ADMIN
        )

        response = self.client.delete(
            self.get_detail_endpoint(
                key=self.get_lookup_key(admin_membership_instance), site_slug=site.slug
            ),
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("app_role", [AppRole.STAFF, AppRole.SUPERADMIN])
    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_delete_success_app_admin(self, app_role, role):
        site, _ = factories.get_site_with_app_admin(
            self.client, Visibility.PUBLIC, app_role
        )
        instance = factories.MembershipFactory.create(site=site, role=role)

        response = self.client.delete(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
        )

        assert response.status_code == 204
