import json

import pytest
from rest_framework.reverse import reverse

from backend.models import JoinRequest, Membership
from backend.models.constants import AppRole, Role, Visibility
from backend.models.join_request import JoinRequestReason, JoinRequestStatus
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SiteContentDestroyApiTestMixin,
    WriteApiTestMixin,
)

approve_viewname = "api:joinrequest-approve"
ignore_viewname = "api:joinrequest-ignore"
reject_viewname = "api:joinrequest-reject"


class TestJoinRequestEndpoints(
    WriteApiTestMixin,
    SiteContentCreateApiTestMixin,
    SiteContentDestroyApiTestMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    """
    End-to-end tests that the join request endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:joinrequest-list"
    API_DETAIL_VIEW = "api:joinrequest-detail"
    REASON_NOTE = "Test reason note"

    model = JoinRequest

    def create_minimal_instance(self, site, visibility=None):
        return factories.JoinRequestFactory(
            site=site,
            status=JoinRequestStatus.PENDING,
            reason=JoinRequestReason.OTHER,
            reason_note=self.REASON_NOTE,
        )

    def get_expected_response(self, instance, site):
        return {
            "created": instance.created.astimezone().isoformat(),
            "createdBy": instance.created_by.email,
            "lastModified": instance.last_modified.astimezone().isoformat(),
            "lastModifiedBy": instance.last_modified_by.email,
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
            "user": {
                "id": int(instance.user.id),
                "email": instance.user.email,
                "firstName": instance.user.first_name,
                "lastName": instance.user.last_name,
            },
            "status": "pending",
            "reason": "other",
            "reasonNote": self.REASON_NOTE,
        }

    def get_expected_detail_response(self, instance, site):
        return self.get_expected_response(instance, site)

    def get_valid_data(self, site=None):
        return {
            "user": factories.UserFactory().email,
            "status": "pending",
            "reason": "other",
            "reason_note": self.REASON_NOTE,
        }

    def get_valid_data_with_nulls(self, site=None):
        return self.get_valid_data(site)

    def add_expected_defaults(self, data):
        return data

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.user.email == expected_data["user"]
        assert actual_instance.get_status_display().lower() == expected_data["status"]
        assert actual_instance.get_reason_display().lower() == expected_data["reason"]
        assert actual_instance.reason_note == expected_data["reason_note"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["user"]["email"] == expected_data["user"]
        assert actual_response["status"] == expected_data["status"]
        assert actual_response["reason"] == expected_data["reason"]
        assert actual_response["reasonNote"] == expected_data["reason_note"]

    def assert_created_instance(self, pk, data):
        instance = JoinRequest.objects.get(pk=pk)
        assert instance.user.email == data["user"]
        assert instance.get_status_display().lower() == data["status"]
        assert instance.get_reason_display().lower() == data["reason"]
        assert instance.reason_note == data["reason_note"]

    def assert_created_response(self, expected_data, actual_response):
        self.assert_update_response(expected_data, actual_response)

    def create_original_instance_for_patch(self, site):
        return factories.JoinRequestFactory(
            site=site,
            user=factories.UserFactory(),
            status=JoinRequestStatus.PENDING,
            reason=JoinRequestReason.OTHER,
            reason_note=self.REASON_NOTE,
        )

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass

    @pytest.mark.django_db
    def test_join_request_unique_validation(self):
        """
        Test that a join request cannot be created for the same user and site.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory()
        factories.JoinRequestFactory(site=site, user=user)

        data = {
            "user": user.email,
            "status": "pending",
            "reason": "other",
            "reason_note": self.REASON_NOTE,
        }
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )
        assert response.status_code == 400

    @pytest.mark.skip("This endpoint has custom permissions")
    def test_detail_member_access(self, role):
        # See custom permission tests instead
        pass

    @pytest.mark.skip("This endpoint has custom permissions")
    def test_detail_team_access(self):
        # See custom permission tests instead
        pass

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_detail_403_for_non_admins(self, role, visibility):
        site = factories.SiteFactory.create(visibility=visibility)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=visibility)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_detail_language_admin_access(self, visibility):
        site = factories.SiteFactory.create(visibility=visibility)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=visibility)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    @pytest.mark.parametrize("app_role", AppRole)
    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_detail_app_admin_access(self, visibility, app_role):
        site = self.create_site_with_app_admin(visibility, app_role)

        instance = self.create_minimal_instance(site=site, visibility=visibility)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_list_empty_for_non_admins(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        factories.JoinRequestFactory.create(site=site)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_list_language_admin_access(self, visibility):
        site = factories.SiteFactory.create(visibility=visibility)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

    @pytest.mark.parametrize("app_role", AppRole)
    @pytest.mark.parametrize("visibility", Visibility)
    @pytest.mark.django_db
    def test_list_app_admin_access(self, visibility, app_role):
        site = self.create_site_with_app_admin(visibility, app_role)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

    #
    # tests for approve and ignore actions ---------------------------
    #

    def get_action_endpoint(self, viewname, site_slug, key):
        return reverse(viewname, current_app=self.APP_NAME, args=[site_slug, str(key)])

    def get_approve_endpoint(self, key, site_slug):
        return self.get_action_endpoint(approve_viewname, site_slug, key)

    def get_ignore_endpoint(self, key, site_slug):
        return self.get_action_endpoint(ignore_viewname, site_slug, key)

    def get_reject_endpoint(self, key, site_slug):
        return self.get_action_endpoint(reject_viewname, site_slug, key)

    @pytest.mark.parametrize(
        "viewname", [approve_viewname, ignore_viewname, reject_viewname]
    )
    @pytest.mark.django_db
    def test_actions_404_missing_site(self, viewname):
        join_request = factories.JoinRequestFactory.create()
        response = self.client.post(
            self.get_action_endpoint(
                viewname, key=str(join_request.id), site_slug="fake-slug"
            )
        )

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "viewname", [approve_viewname, ignore_viewname, reject_viewname]
    )
    @pytest.mark.django_db
    def test_actions_404_missing_join_request(self, viewname):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        response = self.client.post(
            self.get_action_endpoint(viewname, key="fake-key", site_slug=site.slug)
        )

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "viewname", [approve_viewname, ignore_viewname, reject_viewname]
    )
    @pytest.mark.django_db
    def test_actions_403_admin_of_other_site(self, viewname):
        _, user = factories.get_site_with_member(Visibility.PUBLIC, Role.LANGUAGE_ADMIN)
        self.client.force_authenticate(user=user)

        other_site = factories.SiteFactory.create()
        join_request = factories.JoinRequestFactory.create(site=other_site)

        response = self.client.post(
            self.get_action_endpoint(
                viewname, key=str(join_request.id), site_slug=other_site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.parametrize(
        "viewname", [approve_viewname, ignore_viewname, reject_viewname]
    )
    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_actions_403_not_admin(self, role, viewname):
        site, user = factories.get_site_with_member(Visibility.PUBLIC, role)
        self.client.force_authenticate(user=user)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_action_endpoint(
                viewname, key=str(join_request.id), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.parametrize(
        "viewname", [approve_viewname, ignore_viewname, reject_viewname]
    )
    @pytest.mark.django_db
    def test_actions_403_staff(self, viewname):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, AppRole.STAFF)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_action_endpoint(
                viewname, key=str(join_request.id), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_approve_400_missing_role(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, AppRole.SUPERADMIN)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_approve_endpoint(
                key=str(join_request.id), site_slug=join_request.site.slug
            )
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_approve_400_invalid_role(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, AppRole.SUPERADMIN)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_approve_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "princess"}),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_approve_success_admin(self):
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_approve_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_approved(join_request, site)

    @pytest.mark.django_db
    def test_approve_success_superadmin(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, AppRole.SUPERADMIN)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_approve_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_approved(join_request, site)

    def assert_request_approved(self, join_request, site):
        membership = Membership.objects.filter(
            site=site, user=join_request.user, role=Role.MEMBER
        )
        assert membership.count() == 1
        updated_join_request = JoinRequest.objects.get(pk=join_request.pk)
        assert updated_join_request.status == JoinRequestStatus.APPROVED

    @pytest.mark.django_db
    def test_ignore_success_admin(self):
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_ignore_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_ignored(join_request)

    @pytest.mark.django_db
    def test_ignore_success_superadmin(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, AppRole.SUPERADMIN)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_ignore_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_ignored(join_request)

    def assert_request_ignored(self, join_request):
        updated_join_request = JoinRequest.objects.get(pk=join_request.pk)
        assert updated_join_request.status == JoinRequestStatus.IGNORED

    @pytest.mark.django_db
    def test_reject_success_admin(self):
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_reject_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_rejected(join_request)

    @pytest.mark.django_db
    def test_reject_success_superadmin(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, AppRole.SUPERADMIN)

        join_request = factories.JoinRequestFactory.create(site=site)

        response = self.client.post(
            self.get_reject_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_rejected(join_request)

    def assert_request_rejected(self, join_request):
        updated_join_request = JoinRequest.objects.get(pk=join_request.pk)
        assert updated_join_request.status == JoinRequestStatus.REJECTED
