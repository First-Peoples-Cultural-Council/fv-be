import json

import jwt
import requests
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions

from backend.models import User


class UserAuthentication(authentication.BaseAuthentication):
    """
    JWT Token Decode and Map to User
    """

    def refresh_jwk(self):
        certs_response = requests.get(settings.JWT["JWKS_URL"])
        jwks = json.loads(certs_response.text)
        self.jwks = jwks

    def __init__(self):
        self.jwks = None
        self.refresh_jwk()

    def authenticate(self, request):
        """Verify the JWT token and find (or create) the correct user in the DB"""
        auth = request.META.get("HTTP_AUTHORIZATION", None)

        if not auth:
            return AnonymousUser, None

        try:
            scheme, token = auth.split()
        except ValueError:
            raise exceptions.AuthenticationFailed(
                "Invalid format for authorization header"
            )
        if scheme != "Bearer":
            raise exceptions.AuthenticationFailed("Authorization header invalid")

        if not token:
            raise exceptions.AuthenticationFailed("No token found")

        token_validation_errors = []

        jwks_client = jwt.PyJWKClient(settings.JWT["JWKS_URL"])

        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
        except Exception as exc:
            token_validation_errors.append(exc)
            raise Exception(str(exc))

        try:
            user_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.JWT["AUDIENCE"],
                options={"verify_exp": True},
            )
        except jwt.InvalidTokenError as exc:
            token_validation_errors.append(exc)
            raise Exception(exc)

        if not user_token:
            raise exceptions.AuthenticationFailed(
                "Failed decode: {}",
                "\n".join([str(error) for error in token_validation_errors]),
            )

        try:
            user = User.objects.get(id=user_token["sub"])
            return user, None
        except User.DoesNotExist:
            # resolve user info
            userinfo_request = requests.get(
                settings.JWT["USERINFO_URL"], headers={"Authorization": auth}
            )

            if userinfo_request.status_code == 200:
                email = userinfo_request.json()["email"]
                user = User.objects.create(id=user_token["sub"], email=email)
                return user, None
