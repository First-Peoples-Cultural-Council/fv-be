"""
Settings for automated testing only.
"""

from .settings import *  # noqa

# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

REST_FRAMEWORK.update(  # noqa F405
    {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            # remove jwt auth for the test runner
            "rest_framework.authentication.SessionAuthentication",
            "rest_framework.authentication.BasicAuthentication",
        ],
    }
)

# Disable AWS file storage during tests
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
MEDIA_ROOT = BASE_DIR / "backend" / "tests" / "tmp"  # noqa F405
