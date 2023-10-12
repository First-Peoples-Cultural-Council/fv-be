import json

import pytest
from django.core import mail
from django.urls import reverse

from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import BaseApiTest, WriteApiTestMixin


class TestContactUsEndpoint(WriteApiTestMixin, BaseApiTest):
    content_type = "application/json"

    def get_endpoint(self, site_slug):
        return reverse(
            "api:contact-us-list", current_app=self.APP_NAME, args=[site_slug]
        )

    def get_valid_data(self):
        return json.dumps(
            {
                "name": "Test User",
                "email": "testuser@example.com",
                "message": "Test message",
            }
        )

    @pytest.mark.django_db
    def test_contact_us_404(self):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_endpoint("missing-slug"))
        assert response.status_code == 404
        assert len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_contact_us_403(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.MEMBERS)

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_endpoint(site.slug))
        assert response.status_code == 403
        assert len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_contact_us_anonymous(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)

        user = factories.get_anonymous_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_endpoint(site.slug))
        assert response.status_code == 403
        assert len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_contact_us_non_member_user(self):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_email=["contactemail@email.com"],
        )

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_endpoint(site.slug),
            data=self.get_valid_data(),
            content_type=self.content_type,
        )
        assert response.status_code == 202
        assert len(mail.outbox) == 1

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_contact_us_member_user(self, role):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.MEMBERS,
            contact_email=["contactemail@email.com"],
        )

        user = factories.UserFactory.create()
        factories.MembershipFactory.create(site=site, user=user, role=role)
        self.client.force_authenticate(user=user)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_endpoint(site.slug),
            data=self.get_valid_data(),
            content_type=self.content_type,
        )
        assert response.status_code == 202
        assert len(mail.outbox) == 1

    @pytest.mark.parametrize(
        "data",
        [
            {
                "name": "Test Username",
                "email": "testuser@example.com",
                "message": "Test message restricted word.",
            },
            {
                "name": "Test Username",
                "email": "testrestrictedemail@example.com",
                "message": "Test message.",
            },
            {
                "name": "Test Restricted Username",
                "email": "testuser@example.com",
                "message": "Test message.",
            },
        ],
    )
    @pytest.mark.django_db
    def test_contact_us_restricted_word(self, data):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_email=["contactemail@email.com"],
        )
        factories.AppJsonFactory.create(
            key="contact_us_excluded_words", json=["restricted"]
        )

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_endpoint(site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )
        assert response.status_code == 500
        assert len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_contact_us_invalid_from_email(self):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_email=["contactemail@email.com"],
        )

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        assert len(mail.outbox) == 0

        data = {
            "name": "Test User",
            "email": "testuser not valid email",
            "message": "Test message",
        }

        response = self.client.post(
            self.get_endpoint(site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )
        assert response.status_code == 500
        assert len(mail.outbox) == 0

    @pytest.mark.parametrize(
        "create_fallback, expected_response", ((True, 202), (False, 500))
    )
    @pytest.mark.django_db
    def test_contact_us_fallback_email(self, create_fallback, expected_response):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)

        if create_fallback:
            factories.AppJsonFactory.create(
                key="contact_us_default_emails", json=["fallback@email.com"]
            )

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_endpoint(site.slug),
            data=self.get_valid_data(),
            content_type=self.content_type,
        )
        assert response.status_code == expected_response
        assert len(mail.outbox) == 1 if create_fallback else len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_contact_us_no_emails_available(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_endpoint(site.slug),
            data=self.get_valid_data(),
            content_type=self.content_type,
        )
        assert response.status_code == 500
        assert len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_contact_us_multiple_emails_and_users(self):
        user_one = factories.UserFactory.create()
        user_two = factories.UserFactory.create()
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_email=["contactemailone@email.com", "contactemailtwo@email.com"],
        )
        site.contact_users.add(user_one)
        site.contact_users.add(user_two)
        site.save()

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        assert len(mail.outbox) == 0

        response = self.client.post(
            self.get_endpoint(site.slug),
            data=self.get_valid_data(),
            content_type=self.content_type,
        )
        assert response.status_code == 202
        assert len(mail.outbox) == 1
        for email in mail.outbox[0].to:
            assert email in [
                site.contact_email[0],
                site.contact_email[1],
                user_one.email,
                user_two.email,
            ]
