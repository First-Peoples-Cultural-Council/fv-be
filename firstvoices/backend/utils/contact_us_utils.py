import logging

from django.core.exceptions import ImproperlyConfigured

from backend.models import AppJson


def get_fallback_emails():
    """
    Returns the list of default emails to use if no emails or users are set on the site contact_users and
    contact_emails fields. The list of default emails are set in the AppJson model with the key
    'contact_us_default_emails'.
    """

    logger = logging.getLogger(__name__)
    if AppJson.objects.filter(key="contact_us_default_emails").count() == 0:
        raise ImproperlyConfigured(
            'No default email set in AppJson model with key "contact_us_default_email".'
        )
    else:
        logger.warning("The fallback email will be used.")

        # Validate that the default emails are a list of strings
        default_email = AppJson.objects.get(key="contact_us_default_emails").json
        if not isinstance(default_email, list) or not all(
            isinstance(email, str) for email in default_email
        ):
            raise ImproperlyConfigured(
                'The "contact_us_default_emails" field in AppJson model must be a list of '
                "emails."
            )

        return default_email
