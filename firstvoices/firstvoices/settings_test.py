"""
Settings for automated testing only.
"""

from .settings import *  # noqa

# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "djcelery.contrib.test_runner.CeleryTestSuiteRunner"

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
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_ROOT = BASE_DIR / "backend" / "tests" / "tmp"  # noqa F405
