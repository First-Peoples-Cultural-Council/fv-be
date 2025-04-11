import json

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories


class SuperAdminAsyncJobPermissionsMixin:
    """
    Permissions tests for APIs that require superadmin permissions to access and create jobs.
    """

    @pytest.mark.django_db
    def test_list_403_non_member(self):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "role",
        [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    def test_list_empty_non_superuser(self, role):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.create_minimal_instance(site=site, visibility=None)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 0
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_empty_staff(self):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        factories.AppMembershipFactory.create(user=user, role=AppRole.STAFF)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 0
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_get_403_non_member(self):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "role",
        [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    def test_get_403_non_superuser(self, role):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        self.client.force_authenticate(user=user)
        instance = self.create_minimal_instance(site=site, visibility=None)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_get_403_staff(self):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        factories.AppMembershipFactory.create(user=user, role=AppRole.STAFF)
        self.client.force_authenticate(user=user)
        instance = self.create_minimal_instance(site=site, visibility=None)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_post_403_non_member(self):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        self.client.force_authenticate(user=user)

        data = {}

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data=data, format="json"
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "role",
        [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    def test_post_403_non_superuser(self, role):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        data = {}

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data=data, format="json"
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_post_403_staff(self):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        factories.AppMembershipFactory.create(user=user, role=AppRole.STAFF)
        self.client.force_authenticate(user=user)

        data = {}

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data=data, format="json"
        )

        assert response.status_code == 403


class WriteApiTestMixin:
    """Common functions for Create and Update API tests"""

    content_type = "application/json"

    def get_invalid_data(self):
        """Returns an invalid data object suitable for failing create/update requests"""
        return {}

    def get_valid_data(self, site=None):
        """Returns a valid data object suitable for create/update requests"""
        raise NotImplementedError

    def get_valid_data_with_nulls(self, site=None):
        """Returns a valid data object with all optional fields omitted (including strings that can be blank),
        suitable for create/update requests"""
        raise NotImplementedError

    def get_valid_data_with_null_optional_charfields(self, site=None):
        """Returns a valid data object that includes all optional charfields set to None"""
        raise NotImplementedError

    def add_expected_defaults(self, data):
        """Returns a data object with default values filled in for all non-required fields"""
        raise NotImplementedError

    def format_upload_data(self, data):
        """Subclasses can override this to support something other than json"""
        return json.dumps(data)
