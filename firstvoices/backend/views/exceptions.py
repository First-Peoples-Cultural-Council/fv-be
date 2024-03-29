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
