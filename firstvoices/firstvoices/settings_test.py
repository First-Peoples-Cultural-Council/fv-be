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
