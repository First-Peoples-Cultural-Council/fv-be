import json

import pytest

from backend.models import Membership
from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentDetailApiTestMixin,
    SiteContentListApiTestMixin,
)


class TestMembershipEndpoints(
    SiteContentListApiTestMixin,
    SiteContentDetailApiTestMixin,
    BaseSiteContentApiTest,
):
    """
    End-to-end tests that the join request endpoints have the expected behaviour. Includes custom permission tests.
    """

    API_LIST_VIEW = "api:membership-list"
    API_DETAIL_VIEW = "api:membership-detail"

    model = Membership

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
            "role": Role.MEMBER.label,
        }

    def get_expected_detail_response(self, instance, site):
        expected = self.get_expected_response(instance, site)
        return expected

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
