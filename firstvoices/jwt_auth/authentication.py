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
        raise exceptions.AuthenticationFailed("Invalid format for authorization header")
    if scheme != "Bearer":
        raise exceptions.AuthenticationFailed("Authorization header invalid")
    if not token:
        raise exceptions.AuthenticationFailed("No token found")
    return token


def get_signing_key(token):
    jwks_client = jwt.PyJWKClient(settings.JWT["JWKS_URL"], cache_keys=True)

    try:
        return jwks_client.get_signing_key_from_jwt(token)
    except Exception as exc:
        raise exceptions.AuthenticationFailed(str(exc))


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
        raise exceptions.AuthenticationFailed(exc)

    if not user_token:
        raise exceptions.AuthenticationFailed(
            "Failed to decode user authorization token"
        )

    return user_token


def get_or_create_user_for_token(user_token, auth):
    user_model = get_user_model()
    sub = user_token["sub"]

    try:
        # try to find existing account for this sub
        return user_model.objects.get(sub=sub)

    except user_model.DoesNotExist:
        # try to find existing account for this email, with a blank sub (migrated or added manually)
        email = retrieve_email_for_token(auth)

        try:
            user = user_model.objects.get(sub=None, email=email)
            user.sub = sub
            user.save()
            return user

        except user_model.DoesNotExist:
            # try to add new user
            try:
                return user_model.objects.create(sub=sub, email=email)

            except IntegrityError:
                raise exceptions.AuthenticationFailed(
                    "Can't add user account because that email is already in use."
                )


def retrieve_email_for_token(auth):
    userinfo_response = requests.get(
        settings.JWT["USERINFO_URL"], headers={"Authorization": auth}
    )

    if userinfo_response.status_code == 200:
        return userinfo_response.json()["email"]

    else:
        raise exceptions.AuthenticationFailed("Failed to resolve user information")


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
