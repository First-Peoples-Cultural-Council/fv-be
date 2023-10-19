from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from backend.views.exceptions import ContactUsError


@shared_task
def send_contact_us_email(name, from_email, message, to_email_list):
    """
    Formats and sends a contact-us email using the email backend specified in settings.py
    """
    try:
        # Format the final email
        final_message = (
            "The following message was sent from the contact us form on the FirstVoices website:\n\n"
            f"Name: {name}\n"
            f"Email: {from_email}\n\n"
            f"Message:\n{message}\n"
        )
        # Send the email
        send_mail(
            subject=f"Contact Us Form Submission from {name} ({from_email})",
            message=final_message,
            recipient_list=to_email_list,
            from_email=settings.EMAIL_SENDER_ADDRESS,
        )
    except (ConnectionRefusedError, SMTPException) as e:
        raise ContactUsError(f"Contact us email failed to send. Error: {e}")
