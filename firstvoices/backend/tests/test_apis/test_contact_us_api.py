import json
from smtplib import SMTPException
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from backend.models import Site
from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_api_test import BaseApiTest, WriteApiTestMixin


class TestContactUsEndpoint(WriteApiTestMixin, BaseApiTest):
    content_type = "application/json"
    contact_emails = "contact@email.com"
    contact_email_list = ["contactemailone@email.com", "contactemailtwo@email.com"]

    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        # Sets the celery tasks to run synchronously for testing
        settings.CELERY_TASK_ALWAYS_EAGER = True

    def get_endpoint(self, site_slug):
        return reverse(
            "api:contact-us-list", current_app=self.APP_NAME, args=[site_slug]
        )

    def get_valid_data(self, site=None):
        return json.dumps(
            {
                "name": "Test User",
                "email": "testuser@example.com",
                "message": "Test message",
            }
        )

    @pytest.mark.django_db
    def test_contact_us_post_404(self):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_endpoint("missing-slug"))
        assert response.status_code == 404
        assert len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_contact_us_post_403(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.MEMBERS)

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_endpoint(site.slug))
        assert response.status_code == 403
        assert len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_contact_us_post_anonymous(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)

        user = factories.get_anonymous_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_endpoint(site.slug))
        assert response.status_code == 403
        assert len(mail.outbox) == 0

    @pytest.mark.django_db
    def test_post_non_member_user(self):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=[self.contact_emails],
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

    @pytest.mark.parametrize(
        "exception",
        [ConnectionRefusedError("Test exception"), SMTPException("Test exception")],
    )
    @pytest.mark.django_db
    def test_post_smtp_connection_refused(self, caplog, exception):
        caplog.set_level("INFO")
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=[self.contact_emails],
        )

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        assert len(mail.outbox) == 0

        with patch("backend.tasks.send_email_tasks.send_mail") as mocked_mail:
            mocked_mail.side_effect = exception

            response = self.client.post(
                self.get_endpoint(site.slug),
                data=self.get_valid_data(),
                content_type=self.content_type,
            )
            assert response.status_code == 202
            assert len(mail.outbox) == 0
            assert f"Failed to send email. Error: {exception}" in caplog.text

        assert (
            "Task started." in caplog.text
        )  # No additional info in async send_email_task task.
        assert "Task ended." in caplog.text

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_post_member_user(self, role):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.MEMBERS,
            contact_emails=[self.contact_emails],
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
    def test_post_restricted_word(self, data):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=[self.contact_emails],
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

    @pytest.mark.parametrize(
        "data",
        [
            {
                "name": "Test Username",
                "email": "testuser@example.com",
                "message": "",
            },
            {
                "name": "Test Username",
                "email": "",
                "message": "Test message.",
            },
            {
                "name": "",
                "email": "testuser@example.com",
                "message": "Test message.",
            },
            {
                "name": "Test Username",
                "email": "testuser@example.com",
            },
            {
                "name": "Test Username",
                "message": "Test message.",
            },
            {
                "email": "testuser@example.com",
                "message": "Test message.",
            },
        ],
    )
    @pytest.mark.django_db
    def test_post_blank_fields(self, data):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=[self.contact_emails],
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
    def test_post_invalid_restricted_word_list_set(self):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=[self.contact_emails],
        )
        factories.AppJsonFactory.create(
            key="contact_us_excluded_words", json={"invalid": "not a list of strings"}
        )

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
    def test_post_invalid_from_email(self):
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=[self.contact_emails],
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
    def test_post_fallback_email(self, create_fallback, expected_response):
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
    def test_post_no_emails_available(self):
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
    def test_post_multiple_emails_and_users(self):
        user_one = factories.UserFactory.create()
        user_two = factories.UserFactory.create()
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=self.contact_email_list,
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
                site.contact_emails[0],
                site.contact_emails[1],
                user_one.email,
                user_two.email,
            ]

    @pytest.mark.django_db
    def test_contact_us_get(self):
        user_one = factories.UserFactory.create()
        user_two = factories.UserFactory.create()
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=self.contact_email_list,
        )
        site.contact_users.add(user_one)
        site.contact_users.add(user_two)
        site.save()

        site = Site.objects.get(slug="test")
        assert site.contact_users.count() == 2
        assert len(site.contact_emails) == 2

        factories.MembershipFactory.create(
            user=user_one, site=site, role=Role.LANGUAGE_ADMIN
        )

        self.client.force_authenticate(user=user_one)

        response = self.client.get(self.get_endpoint(site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)

        email_list = response_data[0]["emailList"]
        assert len(email_list) == 4

        assert site.contact_emails[0] in email_list
        assert site.contact_emails[1] in email_list
        assert site.contact_users.all()[0].email in email_list
        assert site.contact_users.all()[1].email in email_list

    @pytest.mark.django_db
    def test_contact_us_get_404(self):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_endpoint("missing-slug"))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_contact_us_get_403(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.MEMBERS)

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_endpoint(site.slug))
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "role, expected_response_status_code",
        [
            (Role.MEMBER, 403),
            (Role.EDITOR, 403),
            (Role.ASSISTANT, 403),
            (Role.LANGUAGE_ADMIN, 200),
            (None, 403),
        ],
    )
    @pytest.mark.django_db
    def test_contact_us_get_roles(self, role, expected_response_status_code):
        user_one = factories.UserFactory.create()
        user_two = factories.UserFactory.create()
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=self.contact_email_list,
        )
        site.contact_users.add(user_one)
        site.contact_users.add(user_two)
        site.save()

        site = Site.objects.get(slug="test")
        assert site.contact_users.count() == 2
        assert len(site.contact_emails) == 2

        if role:
            factories.MembershipFactory.create(user=user_one, site=site, role=role)

        self.client.force_authenticate(user=user_one)

        response = self.client.get(self.get_endpoint(site.slug))
        assert response.status_code == expected_response_status_code

    @pytest.mark.django_db
    def test_contact_us_get_fallback_email(self):
        user_one = factories.UserFactory.create()
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=[],
        )
        fallback_email_list = self.contact_email_list
        factories.AppJsonFactory.create(
            key="contact_us_default_emails", json=fallback_email_list
        )

        assert site.contact_users.count() == 0
        assert len(site.contact_emails) == 0

        factories.MembershipFactory.create(
            user=user_one, site=site, role=Role.LANGUAGE_ADMIN
        )

        self.client.force_authenticate(user=user_one)

        response = self.client.get(self.get_endpoint(site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)

        email_list = response_data[0]["emailList"]
        assert len(email_list) == 2

        assert self.contact_email_list[0] in email_list
        assert self.contact_email_list[1] in email_list

    @pytest.mark.django_db
    def test_invalid_fallback_email_set(self):
        user_one = factories.UserFactory.create()
        site = factories.SiteFactory.create(
            slug="test",
            visibility=Visibility.PUBLIC,
            contact_emails=[],
        )
        factories.AppJsonFactory.create(
            key="contact_us_default_emails",
            json={"invalid": "not a list of email strings"},
        )

        factories.MembershipFactory.create(
            user=user_one, site=site, role=Role.LANGUAGE_ADMIN
        )

        self.client.force_authenticate(user=user_one)

        with pytest.raises(ImproperlyConfigured):
            self.client.get(self.get_endpoint(site.slug))
