import json
import logging

import pytest
from django.core import mail
from rest_framework.reverse import reverse

from backend.models import JoinRequest, Membership
from backend.models.constants import AppRole, Role, Visibility
from backend.models.join_request import JoinRequestReasonChoices, JoinRequestStatus
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SiteContentDestroyApiTestMixin,
    WriteApiTestMixin,
)
from backend.views.utils import get_site_url_from_appjson

TEST_BASE_FRONTEND_URL = "https://test.com"

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
        join_request = factories.JoinRequestFactory(
            site=site,
            status=JoinRequestStatus.PENDING,
            reason_note=self.REASON_NOTE,
        )
        factories.JoinRequestReasonFactory.create(join_request=join_request)
        return join_request

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
            "reasons": [{"reason": "other"}],
            "reasonNote": self.REASON_NOTE,
        }

    def get_expected_detail_response(self, instance, site):
        return self.get_expected_response(instance, site)

    def get_valid_data(self, site=None):
        return {
            "reasons": [{"reason": "other"}],
            "reason_note": self.REASON_NOTE,
        }

    def get_valid_data_with_nulls(self, site=None):
        return self.get_valid_data(site)

    def add_expected_defaults(self, data):
        return data

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.user.email == expected_data["user"]
        assert actual_instance.get_status_display().lower() == expected_data["status"]
        self.assert_reason_fields(expected_data, actual_instance)

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["reasons"][0] == expected_data["reasons"][0]
        assert actual_response["reasonNote"] == expected_data["reason_note"]

        reasons = actual_response["reasons"]
        assert len(reasons) == len(expected_data["reasons"])

    def assert_created_instance(self, pk, data):
        instance = JoinRequest.objects.get(pk=pk)
        self.assert_reason_fields(data, instance)

    def assert_reason_fields(self, data, instance):
        assert instance.reason_note == data["reason_note"]
        assert instance.reasons_set.count() == len(data["reasons"])
        expected_reason_names = [x["reason"].upper() for x in data["reasons"]]
        for reason in instance.reasons_set.all():
            assert JoinRequestReasonChoices(reason.reason).name in expected_reason_names

    def assert_created_response(self, expected_data, actual_response):
        self.assert_update_response(expected_data, actual_response)

    def create_original_instance_for_patch(self, site):
        request = factories.JoinRequestFactory(
            site=site,
            user=factories.UserFactory(),
            status=JoinRequestStatus.PENDING,
            reason_note=self.REASON_NOTE,
        )
        factories.JoinRequestReasonFactory.create(join_request=request)

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass

    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        # Runs the email sending celery task synchronously during testing
        settings.CELERY_TASK_ALWAYS_EAGER = True

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
            "reasons": [{"reason": "other"}],
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

    @pytest.mark.skip("This endpoint has custom permissions")
    def test_create_private_site_403(self):
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
    def test_actions_404_invalid_join_request(self, viewname):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        response = self.client.post(
            self.get_action_endpoint(viewname, key="fake-key", site_slug=site.slug)
        )

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "viewname", [approve_viewname, ignore_viewname, reject_viewname]
    )
    @pytest.mark.django_db
    def test_actions_404_missing_join_request(self, viewname):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        response = self.client.post(
            self.get_action_endpoint(viewname, key=str(site.id), site_slug=site.slug)
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
    def test_approve_400_already_a_member(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, AppRole.SUPERADMIN)

        join_request = factories.JoinRequestFactory.create(site=site)
        factories.MembershipFactory(user=join_request.user, site=join_request.site)

        response = self.client.post(
            self.get_approve_endpoint(
                key=str(join_request.id), site_slug=join_request.site.slug
            ),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.parametrize("create_frontend_base_url", [True, False])
    @pytest.mark.django_db
    def test_approve_success_admin(self, create_frontend_base_url):
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        if create_frontend_base_url:
            factories.AppJsonFactory.create(
                key="frontend_base_url", json=TEST_BASE_FRONTEND_URL
            )

        join_request = factories.JoinRequestFactory.create(site=site)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_approve_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_approved(join_request, site)
        assert len(mail.outbox) == 1

    @pytest.mark.parametrize("app_role", AppRole)
    @pytest.mark.django_db
    def test_approve_success_superadmin(self, app_role):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, app_role)

        join_request = factories.JoinRequestFactory.create(site=site)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_approve_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_approved(join_request, site)
        assert len(mail.outbox) == 1

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

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_reject_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_rejected(join_request)
        assert len(mail.outbox) == 1

    @pytest.mark.django_db
    def test_reject_success_superadmin(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC, AppRole.SUPERADMIN)

        join_request = factories.JoinRequestFactory.create(site=site)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_reject_endpoint(key=str(join_request.id), site_slug=site.slug),
            data=self.format_upload_data({"role": "member"}),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        self.assert_request_rejected(join_request)
        assert len(mail.outbox) == 1

    def assert_request_rejected(self, join_request):
        updated_join_request = JoinRequest.objects.get(pk=join_request.pk)
        assert updated_join_request.status == JoinRequestStatus.REJECTED

    @pytest.mark.django_db
    def test_only_pending_requests_viewable_in_list(self):
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        factories.JoinRequestFactory.create(site=site, status=JoinRequestStatus.PENDING)
        factories.JoinRequestFactory.create(
            site=site, status=JoinRequestStatus.APPROVED
        )
        factories.JoinRequestFactory.create(site=site, status=JoinRequestStatus.IGNORED)
        factories.JoinRequestFactory.create(
            site=site, status=JoinRequestStatus.REJECTED
        )

        response = self.client.get(self.get_list_endpoint(site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert len(response_data["results"]) == 1
        assert response_data["results"][0]["status"] == "pending"

    @pytest.mark.django_db
    def test_reasons_are_required(self):
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        data = {
            "reasons": [],
            "reason_note": self.REASON_NOTE,
        }

        response = self.client.post(
            self.get_list_endpoint(site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_reasons_are_unique(self):
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        data = {
            "reasons": [{"reason": "other"}, {"reason": "other"}],
            "reason_note": self.REASON_NOTE,
        }

        response = self.client.post(
            self.get_list_endpoint(site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_reason_key_validation(self):
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        data = {
            "reasons": [{"reason": "other"}, {"reason": "invalid"}],
            "reason_note": self.REASON_NOTE,
        }

        response = self.client.post(
            self.get_list_endpoint(site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    def create_join_request(self, site):
        anon_user = factories.UserFactory.create()
        self.client.force_authenticate(user=anon_user)
        assert len(mail.outbox) == 0
        assert JoinRequest.objects.count() == 0
        response = self.client.post(
            self.get_list_endpoint(site.slug),
            data=self.format_upload_data(
                {
                    "user": anon_user.email,
                    "reasons": [{"reason": "other"}],
                    "reason_note": self.REASON_NOTE,
                }
            ),
            content_type=self.content_type,
        )
        assert response.status_code == 201
        assert JoinRequest.objects.count() == 1

    @pytest.mark.parametrize("create_frontend_base_url", [True, False])
    @pytest.mark.django_db
    def test_create_language_admin_email_sent(self, create_frontend_base_url):
        site, _ = factories.get_site_with_member(Visibility.PUBLIC, Role.LANGUAGE_ADMIN)

        if create_frontend_base_url:
            factories.AppJsonFactory.create(
                key="frontend_base_url", json=TEST_BASE_FRONTEND_URL
            )

        self.create_join_request(site)
        assert len(mail.outbox) == 1

    @pytest.mark.django_db
    def test_create_no_language_admin_for_email(self, caplog):
        caplog.set_level(logging.WARNING)
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        self.create_join_request(site)
        assert len(mail.outbox) == 0
        assert (
            f"No language admins found for site {site.slug}. Join request email will not be sent."
            in caplog.text
        )

    @pytest.mark.django_db
    def test_get_base_url_from_appjson(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.AppJsonFactory.create(
            key="frontend_base_url", json=TEST_BASE_FRONTEND_URL
        )
        base_url = get_site_url_from_appjson(site)
        assert base_url == TEST_BASE_FRONTEND_URL + "/" + site.slug + "/"

    @pytest.mark.django_db
    def test_get_base_url_no_appjson(self, caplog):
        caplog.set_level(logging.WARNING)
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        base_url = get_site_url_from_appjson(site)
        assert base_url is None
        assert (
            'No AppJson instance with key "frontend_base_url" found. Site URLs will not be included in join '
            'request emails. Please add a key "frontend_base_url" to AppJson with the base URL of the frontend '
            'as the value string (eg: "https://firstvoices.com").'
        ) in caplog.text

    @pytest.mark.django_db
    def test_create_request_for_private_site(self):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.UserFactory.create()
        self.client.force_authenticate(user=user)

        data = {
            "reasons": [{"reason": "other"}],
            "reason_note": self.REASON_NOTE,
        }
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201
        assert JoinRequest.objects.count() == 1

    @pytest.mark.django_db
    def test_list_order(self):
        # Test that the list endpoint returns join request results ordered by reverse creation date

        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        join_request_one = factories.JoinRequestFactory.create(
            site=site, status=JoinRequestStatus.PENDING
        )
        join_request_two = factories.JoinRequestFactory.create(
            site=site, status=JoinRequestStatus.PENDING
        )
        join_request_three = factories.JoinRequestFactory.create(
            site=site, status=JoinRequestStatus.PENDING
        )

        response = self.client.get(self.get_list_endpoint(site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert len(response_data["results"]) == 3

        assert response_data["results"][0]["id"] == str(join_request_three.id)
        assert response_data["results"][1]["id"] == str(join_request_two.id)
        assert response_data["results"][2]["id"] == str(join_request_one.id)

    @pytest.mark.django_db
    def test_create_multiple_requests_not_possible(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.UserFactory.create()
        self.client.force_authenticate(user=user)

        data = {
            "reasons": [{"reason": "other"}],
            "reason_note": self.REASON_NOTE,
        }
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201
        assert JoinRequest.objects.count() == 1

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400
        assert JoinRequest.objects.count() == 1

    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_create_not_possible_if_already_member(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.UserFactory.create()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        data = {
            "reasons": [{"reason": "other"}],
            "reason_note": self.REASON_NOTE,
        }
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400
        assert JoinRequest.objects.count() == 0
