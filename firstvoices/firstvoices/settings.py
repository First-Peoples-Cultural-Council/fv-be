"""
Django settings for firstvoices project.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from pathlib import Path

from dotenv import load_dotenv

from . import database, jwt

# .env file support
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-5^%n@uxu*tev&gyzsf-2_s8bdr#thg%qbtor3&k0zodl12j-1s"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG: bool = os.environ.get("DEBUG_DISABLE") is None

ALLOWED_HOSTS = [
    os.environ.get("HOST_HEADER"),
    "*.firstvoices.io",
    ".localhost",
    "127.0.0.1",
    "[::1]",
]

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "rules.apps.AutodiscoverRulesConfig",
    "backend",
    "healthcheck",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",  # ugh. sessions. required by admin.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CSRF_TRUSTED_ORIGINS = ["https://*.eks.firstvoices.io"]

ROOT_URLCONF = "firstvoices.urls"

REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # the first 2 are for admin app compatibility
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "backend.jwt_auth.UserAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_PAGINATION_CLASS": "backend.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

# local only
if DEBUG:
    REST_FRAMEWORK.update(
        {
            "DEFAULT_RENDERER_CLASSES": (
                "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
                "rest_framework.renderers.BrowsableAPIRenderer",
            )
        }
    )

    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
    INSTALLED_APPS += ["debug_toolbar"]
    INSTALLED_APPS += ["django_extensions"]
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
        "SHOW_TEMPLATE_CONTEXT": True,
    }
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
    INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]


AUTHENTICATION_BACKENDS = [
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = os.getenv("DJANGO_STATIC_URL", "static/")
STATIC_ROOT = "static"

WSGI_APPLICATION = "firstvoices.wsgi.application"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
    "auth": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "auth",
    },
}

DATABASES = {"default": database.config()}

AUTH_USER_MODEL = "backend.User"

JWT = jwt.config()

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    os.getenv("ALLOWED_ORIGIN"),
]

LANGUAGE_CODE = "en-ca"

TIME_ZONE = "America/Vancouver"

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ADMIN_URL = "admin/"

with open(str(BASE_DIR / "firstvoices" / "templates" / "api-description.md")) as f:
    description = f.read()

# By Default swagger ui is available only to admin user(s). You can change permission classes to change that
# See more configuration options at https://drf-spectacular.readthedocs.io/en/latest/settings.html#settings
SPECTACULAR_SETTINGS = {
    "TITLE": "FirstVoices Backend API",
    "DESCRIPTION": description,
    "VERSION": "2.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
}

# Fixtures directory for initial data
FIXTURES_DIR = BASE_DIR / "backend" / "fixtures"
