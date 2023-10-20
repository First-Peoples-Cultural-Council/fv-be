import logging
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_email_task(subject, message, to_email_list):
    """
    Sends an email using the email backend specified in settings.py
    """
    logger = logging.getLogger(__name__)
    try:
        send_mail(
            subject=subject,
            message=message,
            recipient_list=to_email_list,
            from_email=settings.EMAIL_SENDER_ADDRESS,
        )
    except (ConnectionRefusedError, SMTPException) as e:
        logger.error(f"Failed to send email. Error: {e}")
