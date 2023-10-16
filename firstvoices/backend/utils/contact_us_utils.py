import logging

from backend.models import AppJson
from backend.views.exceptions import ContactUsError


def get_fallback_emails():
    logger = logging.getLogger(__name__)
    if AppJson.objects.filter(key="contact_us_default_emails").count() == 0:
        logger.error(
            'No default email set in AppJson model with key "contact_us_default_email".'
        )
        raise ContactUsError()
    else:
        logger.warning("The fallback email will be used.")

        # Validate that the default emails are a list of strings
        default_email = AppJson.objects.get(key="contact_us_default_emails").json
        if not isinstance(default_email, list) or not all(
            isinstance(email, str) for email in default_email
        ):
            logger.error(
                'The "contact_us_default_emails" field in AppJson model must be a list of emails.'
            )
            raise ContactUsError()

        return default_email
