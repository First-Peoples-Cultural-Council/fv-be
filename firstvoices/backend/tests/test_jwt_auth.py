from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

from backend import jwt_auth
from backend.tests import factories


def mock_userinfo_response(user_email):
    response = MagicMock()
    type(response).status_code = PropertyMock(return_value=200)
    response.json.return_value = {"email": user_email}
    return response


def mock_failed_userinfo_response():
    response = MagicMock()
    type(response).status_code = PropertyMock(return_value=404)
    return response


class TestGetOrCreateUserForToken:
    """
    Tests for jwt_auth.get_or_create_user_for_token
    """

    @pytest.mark.django_db
    def test_existing_user(self):
        user_id = "123-existing-user"
        existing_user = factories.UserFactory.create(id=user_id)

        token = {"sub": user_id}
        found_user = jwt_auth.get_or_create_user_for_token(token, None)

        assert found_user == existing_user

    @pytest.mark.django_db
    def test_new_user(self):
        user_id = "123_new_user"

        existing_user = get_user_model().objects.filter(id=user_id)
        assert existing_user.count() == 0

        with patch(
            "requests.get",
            return_value=mock_userinfo_response("surprising_new_email@email.email"),
        ):
            token = {"sub": user_id}
            found_user = jwt_auth.get_or_create_user_for_token(token, None)

            assert found_user.id == user_id
            new_user = get_user_model().objects.filter(id=user_id)
            assert new_user.count() == 1

    @pytest.mark.django_db
    def test_unclaimed_user(self):
        user_id = "123_new_user"
        user_email = "unclaimed_account@email.email"

        # unclaimed user has email as the id
        factories.UserFactory.create(id=user_email, email=user_email)

        with patch("requests.get", return_value=mock_userinfo_response(user_email)):
            token = {"sub": user_id}
            found_user = jwt_auth.get_or_create_user_for_token(token, None)

            assert found_user.id == user_id
            claimed_user = get_user_model().objects.filter(email=user_email, id=user_id)
            assert claimed_user.count() == 1

    @pytest.mark.django_db
    def test_already_claimed_user(self):
        user_email = "already_in_use@email.email"

        # existing user with the same email, but a different id
        factories.UserFactory.create(id="existing_id-abc123", email=user_email)

        with patch("requests.get", return_value=mock_userinfo_response(user_email)):
            token = {"sub": "new-id-xyz"}

            with pytest.raises(AuthenticationFailed):
                jwt_auth.get_or_create_user_for_token(token, None)

    @pytest.mark.django_db
    def test_userinfo_not_found(self):
        with patch("requests.get", return_value=mock_failed_userinfo_response()):
            token = {"sub": "new-id-xyz"}

            with pytest.raises(AuthenticationFailed):
                jwt_auth.get_or_create_user_for_token(token, None)


# no auth header
# no bearer scheme
# no bearer token
# expired token
# invalid token
# other problems?
