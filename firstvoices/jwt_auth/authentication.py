import logging

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from rest_framework import authentication, exceptions


def extract_bearer_token(auth):
    try:
        scheme, token = auth.split()
    except ValueError:
        raise exceptions.NotAuthenticated("Invalid format for authorization header")
    if scheme != "Bearer":
        raise exceptions.NotAuthenticated("Authorization header invalid")
    if not token:
        raise exceptions.NotAuthenticated("No token found")
    return token


def get_signing_key(token):
    jwks_client = jwt.PyJWKClient(settings.JWT["JWKS_URL"], cache_keys=True)

    try:
        return jwks_client.get_signing_key_from_jwt(token)
    except Exception as exc:
        raise exceptions.NotAuthenticated(str(exc))


def get_user_token(bearer_token, signing_key):
    try:
        user_token = jwt.decode(
            bearer_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.JWT["AUDIENCE"],
            options={"verify_exp": True},
        )
    except jwt.InvalidTokenError as exc:
        raise exceptions.NotAuthenticated(exc)

    if not user_token:
        raise exceptions.NotAuthenticated("Failed to decode user authorization token")

    return user_token


def get_or_create_user_for_token(user_token, auth):
    user_model = get_user_model()
    sub = user_token["sub"]
    user_info = retrieve_user_info_for_token(auth)

    try:
        """Find user by sub"""
        return find_existing_user(sub, user_info)

    except user_model.DoesNotExist:
        """Find user by email"""

        if "email" not in user_info:
            logger = logging.getLogger(__name__)
            logger.error("Identity Token does not contain required email field.")
            raise exceptions.NotAuthenticated(
                "Authentication is currently unavailable."
            )

        try:
            return claim_unclaimed_user(sub, user_info)

        except user_model.DoesNotExist:
            try:
                return add_new_user(sub, user_info)

            except IntegrityError:
                raise exceptions.NotAuthenticated(
                    "Can't add user account because that email is already in use."
                )


def find_existing_user(sub, user_info):
    """Look up user by sub value. Add any missing user info in our db."""

    logger = logging.getLogger(__name__)
    user_model = get_user_model()
    user = user_model.objects.get(sub=sub)

    if user.first_name or user.last_name:
        return user

    # fill in new name fields if empty
    try:
        user.first_name = user_info["given_name"]
        user.last_name = user_info["family_name"]
        user.save()
    except KeyError as e:
        # Configuration problem: name values not available
        logger.error(
            f"Identity Token does not contain required name fields. Error: [{e}] Available fields: [{user_info.keys()}]"
        )

    return user


def claim_unclaimed_user(sub, user_info):
    """Look up user by email address and link it to this token by adding the sub value. Update user info in our db."""
    user_model = get_user_model()

    user = user_model.objects.get(sub=None, email=user_info["email"])
    user.sub = sub

    if "given_name" in user_info:
        user.first_name = user_info["given_name"]

    if "family_name" in user_info:
        user.last_name = user_info["family_name"]

    user.save()

    return user


def add_new_user(sub, user_info):
    user_model = get_user_model()
    first_name = user_info["given_name"] if "given_name" in user_info else ""
    last_name = user_info["family_name"] if "family_name" in user_info else ""

    return user_model.objects.create(
        sub=sub,
        email=user_info["email"],
        first_name=first_name,
        last_name=last_name,
    )


def retrieve_user_info_for_token(auth):
    userinfo_response = requests.get(
        settings.JWT["USERINFO_URL"], headers={"Authorization": auth}
    )

    if userinfo_response.status_code == 200:
        return userinfo_response.json()

    else:
        raise exceptions.NotAuthenticated("Failed to resolve user information")


class JwtAuthentication(authentication.BaseAuthentication):
    """
    Decode JWT token and map to user
    """

    def authenticate(self, request):
        """Verify the JWT token and find (or create) the correct user in the DB"""

        auth_header = request.META.get("HTTP_AUTHORIZATION", None)

        if not auth_header:
            return AnonymousUser(), None

        bearer_token = extract_bearer_token(auth_header)
        signing_key = get_signing_key(bearer_token)
        user_token = get_user_token(bearer_token, signing_key)
        user = get_or_create_user_for_token(user_token, auth_header)

        return user, None


class JWTScheme(OpenApiAuthenticationExtension):
    """
    Extension for API documentation generator, to document JWT auth scheme.
    """

    target_class = "jwt_auth.authentication.JwtAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name="AUTHORIZATION", token_prefix="Bearer", bearer_format="JWT"
        )
