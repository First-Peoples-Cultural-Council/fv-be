"""
Django settings for firstvoices project.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import logging
import os
from pathlib import Path

import sentry_sdk
from dotenv import load_dotenv
from elasticsearch_dsl import connections
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

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
    "django_celery_beat",
    "rest_framework",
    "drf_spectacular",
    "rules.apps.AutodiscoverRulesConfig",
    "jwt_auth",
    "backend",
    "healthcheck",
    "embed_video",
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

USE_X_FORWARDED_HOST = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
        "jwt_auth.authentication.JwtAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
    "DEFAULT_PAGINATION_CLASS": "backend.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "JSON_UNDERSCOREIZE": {
        "ignore_fields": ("site_data_export",),
    },
}

# LOGGERS
ELASTICSEARCH_LOGGER = "elasticsearch"

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
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "root": {"handlers": ["console"], "level": "WARNING"},
        "loggers": {
            ELASTICSEARCH_LOGGER: {
                "handlers": ["console"],
                "level": "ERROR",  # Change level to INFO to view connection requests
            }
        },
    }

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

AUTH_USER_MODEL = "jwt_auth.User"

JWT = jwt.config()

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
] + os.getenv(
    "ALLOWED_ORIGIN", ""
).split(",")

LANGUAGE_CODE = "en-ca"

TIME_ZONE = "America/Vancouver"

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ADMIN_URL = os.getenv("DJANGO_ADMIN_URL", "admin/")

with open(str(BASE_DIR / "firstvoices" / "templates" / "api-description.md")) as f:
    description = f.read()

# By Default swagger ui is available only to admin user(s). You can change permission classes to change that
# See more configuration options at https://drf-spectacular.readthedocs.io/en/latest/settings.html#settings
SPECTACULAR_SETTINGS = {
    "TITLE": "FirstVoices Backend API",
    "DESCRIPTION": description,
    "VERSION": "2.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
}

# Fixtures directory for initial data
FIXTURES_DIR = BASE_DIR / "backend" / "fixtures"

CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Vancouver"
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL", "amqp://rabbitmq:rabbitmq@localhost:5672//fv"
)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost/0")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_ALWAYS_EAGER = True

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PRIMARY_INDEX = os.getenv("ELASTICSEARCH_PRIMARY_INDEX", "fv")
ELASTICSEARCH_DEFAULT_CONFIG = {"shards": 1, "replicas": 0}
connections.configure(default={"hosts": ELASTICSEARCH_HOST})


# Sentry monitoring configuration settings.
# See docs at https://docs.sentry.io/platforms/python/guides/django/
sentry_logging = LoggingIntegration(
    level=logging.INFO,  # The minimum logging level to capture as breadcrumbs
    event_level=logging.ERROR,  # The minimum logging level to send as events
)
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv(
        "SENTRY_ENVIRONMENT"
    ),  # Sends information to this environment on the dashboard
    release=os.getenv("SENTRY_RELEASE"),  # Tags information with this release version
    traces_sample_rate=os.getenv(
        "SENTRY_TRACES_SAMPLE_RATE", 1.0
    ),  # The percentage of traces to send to sentry (min 0.0, max 1.0)
    send_default_pii=False,  # Disables the sending of personally identifiable information (see
    # https://docs.sentry.io/platforms/python/guides/django/data-collected/)
    request_bodies="never",  # Disables the sending of request bodies
    include_local_variables=False,  # Disables the sending of local variables in the stack trace
    integrations=[
        sentry_logging,
        DjangoIntegration(
            transaction_style="url",
            middleware_spans=True,
            signals_spans=True,
            cache_spans=True,
        ),
    ],
)


# File hosting on AWS S3
# See: https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("MEDIA_UPLOAD_S3_BUCKET")
AWS_S3_REGION_NAME = os.getenv("MEDIA_UPLOAD_S3_REGION", None)
AWS_S3_ENDPOINT_URL = os.getenv("MEDIA_UPLOAD_ENDPOINT", None)
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True  # this is the default setting, just being explicit
AWS_QUERYSTRING_EXPIRE = (
    60 * 60
)  # seconds until a query string expires; this is the default setting


# Disallow import/export unless you have write permission
IMPORT_EXPORT_IMPORT_PERMISSION_CODE = "change"
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = "change"

# Image thumbnail generation settings
IMAGE_SIZES = {"thumbnail": 100, "small": 560, "medium": 1000}

# Backends allowed for embedded videos. Custom backends can be created if other video sites are needed.
EMBED_VIDEO_BACKENDS = (
    "embed_video.backends.YoutubeBackend",
    "embed_video.backends.VimeoBackend",
)
