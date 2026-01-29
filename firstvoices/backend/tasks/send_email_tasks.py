from smtplib import SMTPException

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail

from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE


@shared_task
def send_email_task(subject, message, to_email_list):
    """
    Sends an email using the email backend specified in settings.py
    """
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, "")

    try:
        message = (
            message
            + "\nThis is an automated message. Please do not reply to this email.\n\n"
        )
        send_mail(
            subject=subject,
            message=message,
            recipient_list=to_email_list,
            from_email=settings.EMAIL_SENDER_ADDRESS,
        )
    except (ConnectionRefusedError, SMTPException) as e:
        logger.error(f"Failed to send email. Error: {e}")

    logger.info(ASYNC_TASK_END_TEMPLATE)
