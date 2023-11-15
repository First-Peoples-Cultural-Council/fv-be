from datetime import datetime
from unittest.mock import MagicMock, PropertyMock, patch

import factory
import pytest
from factory.django import DjangoModelFactory
from rest_framework.exceptions import AuthenticationFailed

from . import authentication
from .models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    sub = factory.Sequence(lambda n: "user id %03d" % n)
    email = factory.Sequence(lambda n: "user%03d@email.com" % n)


def mock_userinfo_response(user_email):
    response = MagicMock()
    type(response).status_code = PropertyMock(return_value=200)
    response.json.return_value = {"email": user_email}
    return response


def mock_failed_userinfo_response():
    response = MagicMock()
    type(response).status_code = PropertyMock(return_value=404)
    return response


request = "requests.get"


class TestUserModel:
    @pytest.mark.django_db
    def test_migrated_user(self):
        """
        Users added during migration from the old server will have an email but no sub

        I don't want no subs
        """
        u = User.objects.create(email="cool.email@email.email")
        assert u.id is not None

    @pytest.mark.django_db
    def test_token_user(self):
        """
        Users added during token authentication will have both an email and a sub.
        """
        u = User.objects.create(sub="sample-sub-123", email="another.email@cool.com")
        assert u.id is not None

    @pytest.mark.django_db
    def test_claiming_user(self):
        """
        Verify that a migrated user can have a sub added later
        """
        u = User.objects.create(email="cool.email@email.email")
        assert u.id is not None

        new_sub = "new-sub-xyz"
        u.sub = new_sub
        u.save()

        assert u.sub is new_sub

    @pytest.mark.django_db
    def test_blank_subs_ok(self):
        """
        Verify that multiple users can have blank subs, but non-blank subs must be unique.
        """
        u1 = User.objects.create(email="only.email@email.com")
        u2 = User.objects.create(email="no.subs@email.com")
        assert u1.id is not None
        assert u2.id is not None

    @pytest.mark.django_db
    def test_unique_subs(self):
        """
        Verify that multiple users can have blank subs, but non-blank subs must be unique.
        """
        sub = "same-sub-456"

        u1 = User.objects.create(sub=sub, email="only.email@email.com")
        assert u1.id is not None

        with pytest.raises(Exception):
            User.objects.create(sub=sub, email="no.subs@email.com")


class TestGetOrCreateUserForToken:
    """
    Tests for jwt_auth.get_or_create_user_for_token
    """

    @pytest.mark.django_db
    def test_existing_user(self):
        sub = "123-existing-user"
        existing_user = UserFactory.create(sub=sub)

        token = {"sub": sub}
        found_user = authentication.get_or_create_user_for_token(token, None)

        assert found_user == existing_user

    @pytest.mark.django_db
    def test_new_user(self):
        sub = "123_new_user"

        existing_user = User.objects.filter(sub=sub)
        assert existing_user.count() == 0

        with patch(
            request,
            return_value=mock_userinfo_response("surprising_new_email@email.email"),
        ):
            token = {"sub": sub}
            found_user = authentication.get_or_create_user_for_token(token, None)

            assert found_user.id is not None
            assert found_user.sub == sub
            new_user = User.objects.filter(sub=sub)
            assert new_user.count() == 1

    @pytest.mark.django_db
    def test_unclaimed_user(self):
        sub = "123_new_user"
        email = f"{datetime.timestamp(datetime.now())}@email.email"

        # unclaimed user has email but no sub
        UserFactory.create(sub=None, email=email)

        with patch(request, return_value=mock_userinfo_response(email)):
            token = {"sub": sub}
            found_user = authentication.get_or_create_user_for_token(token, None)

            assert found_user.email == email
            assert found_user.sub == sub
            claimed_user = User.objects.filter(email=email, sub=sub)
            assert claimed_user.count() == 1

    @pytest.mark.django_db
    def test_already_claimed_user(self):
        email = "already_in_use@email.email"

        # existing user with the same email, but a different id
        UserFactory.create(sub="existing_id-abc123", email=email)

        with patch(request, return_value=mock_userinfo_response(email)):
            token = {"sub": "new-id-xyz"}

            with pytest.raises(AuthenticationFailed):
                authentication.get_or_create_user_for_token(token, None)

    @pytest.mark.django_db
    def test_userinfo_not_found(self):
        with patch(request, return_value=mock_failed_userinfo_response()):
            token = {"sub": "new-id-xyz"}

            with pytest.raises(AuthenticationFailed):
                authentication.get_or_create_user_for_token(token, None)


class TestAuthenticate:
    pass
    # no auth header
    # no bearer scheme
    # no bearer token
    # expired token
    # invalid token
    # other problems?
