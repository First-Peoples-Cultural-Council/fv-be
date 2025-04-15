import json

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_api_test import WriteApiTestMixin
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SiteContentDetailApiTestMixin,
    SiteContentListApiTestMixin,
)
from backend.tests.utils import TransactionOnCommitMixin


class SuperAdminAsyncJobPermissionsMixin:
    """
    Permissions tests for APIs that require superadmin permissions to access and create jobs.
    """

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", Role)
    def test_list_empty_for_non_app_admins(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=role
        )
        self.create_minimal_instance(site=site, visibility=None)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 0
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_empty_for_staff(self):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.STAFF
        )
        self.create_minimal_instance(site=site, visibility=None)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 0
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_get_403_non_member(self):
        site, _ = factories.get_site_with_authenticated_nonmember(
            self.client, visibility=Visibility.PUBLIC
        )
        instance = self.create_minimal_instance(site=site, visibility=None)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", Role)
    def test_get_403_non_superuser(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=role
        )
        instance = self.create_minimal_instance(site=site, visibility=None)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_get_403_staff(self):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.STAFF
        )
        instance = self.create_minimal_instance(site=site, visibility=None)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_post_403_non_member(self):
        site, _ = factories.get_site_with_authenticated_nonmember(
            self.client, visibility=Visibility.PUBLIC
        )

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data={}, format="json"
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", Role)
    def test_post_403_non_superuser(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=role
        )

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data={}, format="json"
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_post_403_staff(self):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.STAFF
        )

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), data={}, format="json"
        )

        assert response.status_code == 403


class BaseAsyncSiteContentApiTest(
    TransactionOnCommitMixin,
    WriteApiTestMixin,
    SiteContentCreateApiTestMixin,
    SiteContentListApiTestMixin,
    SiteContentDetailApiTestMixin,
    BaseSiteContentApiTest,
):
    """Base tests for site content APIs that queue async jobs"""

    pass
