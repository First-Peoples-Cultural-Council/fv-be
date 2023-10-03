import json

import pytest

from backend.models import Membership
from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseUncontrolledSiteContentApiTest,
)


class TestMembershipsEndpoint(BaseUncontrolledSiteContentApiTest):
    API_LIST_VIEW = "api:membership-list"
    API_DETAIL_VIEW = "api:membership-detail"

    model = Membership

    def create_minimal_instance(self, site, visibility):
        return factories.MembershipFactory.create(site=site)

    def get_valid_data(self, site=None):
        user = factories.UserFactory.create()
        return {
            "role": "LANGUAGE_ADMIN",
            "user": user.id,
        }


    def get_expected_response(self, instance, site):
        return {
            "id": str(instance.id),
            "role": Role(instance.role).label,
            "user": {
                "id": instance.user.id,  # int, not a uid, so don't str()
                "email": instance.user.email
            },
            "created": instance.created.astimezone().isoformat(),
            "url": f"http://testserver/api/1.0/sites/{site.slug}/memberships/{str(instance.id)}",
        }


    def add_related_objects(self, instance):
        pass

    def assert_related_objects_deleted(self, instance):
        pass


    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access(self, role):
        """ Membership access is not governed by Visibility """
        pass

    @pytest.mark.django_db
    def test_list_team_access(self):
        """ Membership access is not governed by Visibility """
        pass

    @pytest.mark.django_db
    def test_list_minimal(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

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
    def test_detail_member_access(self):
        """ Membership access is not governed by Visibility """
        pass

    @pytest.mark.django_db
    def test_detail_team_access(self):
        """ Membership access is not governed by Visibility """
        pass

    @pytest.mark.django_db
    def test_detail_minimal(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == self.get_expected_detail_response(instance, site)

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.role == Role[expected_data["role"]]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["role"] == Role[expected_data["role"]].label

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        return self.get_expected_response(instance, instance.site)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def get_expected_list_response_item(self, widget, site):
        return self.get_expected_response(widget, site)

    def create_original_instance_for_patch(self, site):
        return factories.MembershipFactory.create(site=site)

    def get_valid_patch_data(self, site=None):
        return {"role": "MEMBER"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.site == original_instance.site
        assert updated_instance.user == original_instance.user

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        assert updated_instance.role == Role[data["role"]]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["role"] == Role[data["role"]].label

    @pytest.mark.django_db
    def test_blocked_for_guests(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        instance = factories.MembershipFactory.create(user=user, site=site, role=Role.MEMBER)

        response = self.client.get(self.get_detail_endpoint(key=str(instance.id), site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []
