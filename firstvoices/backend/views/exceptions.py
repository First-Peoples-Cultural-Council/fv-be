from rest_framework.exceptions import APIException


class CeleryError(APIException):
    status_code = 500
    default_detail = "An error occurred while queuing the celery task."
    default_code = "celery_error"
