from datetime import datetime
from unittest.mock import MagicMock, PropertyMock, patch

import factory
import jwt
import pytest
from factory.django import DjangoModelFactory
from rest_framework.exceptions import AuthenticationFailed

from . import authentication
from .authentication import JwtAuthentication
from .models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    sub = factory.Sequence(lambda n: "user id %03d" % n)
    email = factory.Sequence(lambda n: "user%03d@email.com" % n)
    first_name = factory.Sequence(lambda n: "Firsty%03d" % n)
    last_name = factory.Sequence(lambda n: "Lasty the %03d" % n)


def mock_userinfo_response(user_email, first_name="Firsty", last_name="Lasty"):
    response = MagicMock()
    type(response).status_code = PropertyMock(return_value=200)
    response.json.return_value = {
        "email": user_email,
        "given_name": first_name,
        "family_name": last_name,
    }
    return response


def mock_misconfigured_userinfo_response(value):
    response = MagicMock()
    type(response).status_code = PropertyMock(return_value=200)
    response.json.return_value = value
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
        Users added during token authentication will have both a sub and user info.
        """
        u = User.objects.create(
            sub="sample-sub-123",
            email="another.email@cool.com",
            first_name="Doctor",
            last_name="Forbes",
        )
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
        Verify that multiple users can have blank subs.
        """
        u1 = User.objects.create(email="only.email@email.com")
        u2 = User.objects.create(email="no.subs@email.com")
        assert u1.id is not None
        assert u2.id is not None

    @pytest.mark.django_db
    def test_unique_subs(self):
        """
        Verify that non-blank subs must be unique.
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

        with patch(
            request,
            return_value=mock_userinfo_response(user_email=existing_user.email),
        ):
            found_user = authentication.get_or_create_user_for_token(token, None)
            assert found_user == existing_user

    @pytest.mark.django_db
    def test_new_user(self):
        sub = "123_new_user"

        existing_user = User.objects.filter(sub=sub)
        assert existing_user.count() == 0

        expected_email = "surprising_new_email@email.email"
        expected_first_name = "Firstaline"
        expected_last_name = "Lasterton"

        self.authenticate_and_assert_user(
            expected_email, expected_first_name, expected_last_name, sub
        )

        new_user = User.objects.filter(sub=sub)
        assert new_user.count() == 1

    @pytest.mark.django_db
    def test_unclaimed_user(self):
        sub = "123_new_user"
        email = f"{datetime.timestamp(datetime.now())}@email.email"
        expected_first_name = "Firstiful"
        expected_last_name = "Van Lastname"

        # unclaimed user has email only
        UserFactory.create(sub=None, email=email, first_name="", last_name="")

        self.authenticate_and_assert_user(
            email, expected_first_name, expected_last_name, sub
        )

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

    @pytest.mark.django_db
    def test_userinfo_misconfigured_missing_email_fail(self):
        with patch(
            request,
            return_value=mock_misconfigured_userinfo_response({}),
        ):
            token = {"sub": "123_new_user"}
            with pytest.raises(AuthenticationFailed):
                authentication.get_or_create_user_for_token(token, None)

    @pytest.mark.django_db
    def test_userinfo_misconfigured_missing_names_ignore_claimed_user(self):
        sub = "123_new_user"
        email = f"{datetime.timestamp(datetime.now())}@email.email"
        expected_first_name = "Firstianna"
        expected_last_name = "Lastovich"
        # existing user has no names in db
        UserFactory.create(sub=sub, email=email, first_name="", last_name="")
        with patch(
            request,
            return_value=mock_misconfigured_userinfo_response(
                {"email": email, "name": f"{expected_first_name} {expected_last_name}"}
            ),
        ):
            token = {"sub": "123_new_user"}
            found_user = authentication.get_or_create_user_for_token(token, None)
            assert found_user.email == email
            assert found_user.sub == sub
            assert found_user.first_name == ""
            assert found_user.last_name == ""

    @pytest.mark.django_db
    def test_userinfo_misconfigured_missing_names_ignore_unclaimed_user(self):
        sub = "123_new_user"
        email = f"{datetime.timestamp(datetime.now())}@email.email"
        expected_first_name = "Firstianna"
        expected_last_name = "Lastovich"
        # existing user has no names in db
        UserFactory.create(sub=None, email=email, first_name="", last_name="")

        with patch(
            request,
            return_value=mock_misconfigured_userinfo_response(
                {"email": email, "name": f"{expected_first_name} {expected_last_name}"}
            ),
        ):
            token = {"sub": "123_new_user"}
            found_user = authentication.get_or_create_user_for_token(token, None)
            assert found_user.email == email
            assert found_user.sub == sub
            assert found_user.first_name == ""
            assert found_user.last_name == ""

    @pytest.mark.django_db
    def test_userinfo_misconfigured_missing_names_ignore_new_user(self):
        sub = "123_new_user"
        email = f"{datetime.timestamp(datetime.now())}@email.email"
        expected_first_name = "Firstianna"
        expected_last_name = "Lastovich"

        with patch(
            request,
            return_value=mock_misconfigured_userinfo_response(
                {"email": email, "name": f"{expected_first_name} {expected_last_name}"}
            ),
        ):
            token = {"sub": "123_new_user"}
            found_user = authentication.get_or_create_user_for_token(token, None)
            assert found_user.email == email
            assert found_user.sub == sub
            assert found_user.first_name == ""
            assert found_user.last_name == ""

    @pytest.mark.django_db
    def test_claimed_user_with_no_names(self):
        sub = "123_new_user"
        email = f"{datetime.timestamp(datetime.now())}@email.email"
        expected_first_name = "Firstiful"
        expected_last_name = "Van Lastname"

        # existing user has no names in db
        UserFactory.create(sub=sub, email=email, first_name="", last_name="")

        self.authenticate_and_assert_user(
            email, expected_first_name, expected_last_name, sub
        )

    @pytest.mark.django_db
    def test_unclaimed_user_with_no_names(self):
        sub = "123_new_user"
        email = f"{datetime.timestamp(datetime.now())}@email.email"
        expected_first_name = "Firstilene"
        expected_last_name = "Lasterson"

        # existing user has no names in db
        UserFactory.create(sub=None, email=email, first_name="", last_name="")

        self.authenticate_and_assert_user(
            email, expected_first_name, expected_last_name, sub
        )

    @pytest.mark.django_db
    def test_new_user_with_no_names(self):
        sub = "123_new_user"
        email = f"{datetime.timestamp(datetime.now())}@email.email"
        expected_first_name = "Firster"
        expected_last_name = "Lastt"

        self.authenticate_and_assert_user(
            email, expected_first_name, expected_last_name, sub
        )

    def authenticate_and_assert_user(
        self, email, expected_first_name, expected_last_name, sub
    ):
        with patch(
            request,
            return_value=mock_userinfo_response(
                email, expected_first_name, expected_last_name
            ),
        ):
            token = {"sub": sub}
            found_user = authentication.get_or_create_user_for_token(token, None)

            assert found_user.email == email
            assert found_user.sub == sub
            assert found_user.first_name == expected_first_name
            assert found_user.last_name == expected_last_name


class TestAuthenticate:
    def test_no_auth_header_means_anonymous(self):
        mock_request = MagicMock()
        type(mock_request).META = {}
        auth = JwtAuthentication()
        user, _ = auth.authenticate(mock_request)
        assert user.is_anonymous
        assert not user.is_authenticated

    @pytest.mark.parametrize(
        "token", ["Bearer ", "NotBearer 12345", "12345", "Bearer 12345 and then some"]
    )
    def test_malformed_auth_tokens_fail(self, token):
        mock_request = MagicMock()
        type(mock_request).META = {"HTTP_AUTHORIZATION": token}
        auth = JwtAuthentication()
        with pytest.raises(AuthenticationFailed):
            auth.authenticate(mock_request)

    def test_expired_token_fails(self):
        with patch(
            "jwt.PyJWKClient.get_signing_key_from_jwt",
            side_effect=jwt.ExpiredSignatureError(),
        ):
            mock_request = MagicMock()
            type(mock_request).META = {"HTTP_AUTHORIZATION": "Bearer valid123"}
            auth = JwtAuthentication()
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(mock_request)

    @pytest.mark.parametrize("exception_type", [jwt.InvalidTokenError, jwt.DecodeError])
    def test_invalid_token_fails(self, exception_type):
        with patch("jwt.decode", side_effect=exception_type()), patch(
            "jwt.PyJWKClient.get_signing_key_from_jwt", return_value=MagicMock()
        ):
            mock_request = MagicMock()
            type(mock_request).META = {"HTTP_AUTHORIZATION": "Bearer valid123"}
            auth = JwtAuthentication()
            with pytest.raises(AuthenticationFailed):
                auth.authenticate(mock_request)
