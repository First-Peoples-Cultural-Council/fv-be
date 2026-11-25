from rest_framework.exceptions import APIException


class CeleryError(APIException):
    status_code = 500
    default_detail = "An error occurred while queuing the celery task."
    default_code = "celery_error"


class ElasticSearchConnectionError(APIException):
    status_code = 500
    default_detail = "An error occurred while trying to connect to elastic-search."
    default_code = "elasticsearch_error"


class ContactUsError(APIException):
    status_code = 500
    default_detail = (
        "We have encountered an unexpected error while trying to send the email. Please report this to our "
        "Help Desk."
    )

    default_code = "contact_us_error"


class MatomoConfigurationError(APIException):
    status_code = 503
    default_detail = "Analytics is not configured."
    default_code = "analytics_not_configured"


class MatomoError(APIException):
    status_code = 502
    default_detail = "Analytics is temporarily unavailable."
    default_code = "analytics_unavailable"


class MatomoTimeoutError(APIException):
    status_code = 504
    default_detail = "The analytics service did not respond in time."
    default_code = "analytics_timeout"
