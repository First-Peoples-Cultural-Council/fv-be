import logging
import re
from smtplib import SMTPException

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, parsers, serializers
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.models import AppJson
from backend.views import doc_strings
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin
from backend.views.exceptions import ContactUsError


@extend_schema_view(
    create=extend_schema(
        description="Sends emails to the addresses listed on the site contact_us_form_email field.",
        responses={
            202: OpenApiResponse(description="Success. Email successfully sent."),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
        request=inline_serializer(
            name="Contact Us Form",
            fields={
                "name": serializers.CharField(),
                "email": serializers.CharField(),
                "message": serializers.CharField(),
            },
        ),
    ),
)
class ContactUsView(
    SiteContentViewSetMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    http_method_names = ["post"]
    serializer_class = None
    parser_classes = [
        parsers.FormParser,
        parsers.MultiPartParser,
    ]

    def get_queryset(self):
        return self.get_validated_site()

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        site = self.get_validated_site().first()
        if request.user.is_anonymous:
            return Response(
                {"message": "You must be logged in to send an email."}, status=403
            )
        try:
            to_email_list = site.contact_email
            to_email_list.extend(site.contact_users.values_list("email", flat=True))
            name = request.data["name"]
            from_email = request.data["email"]
            message = request.data["message"]

            # Validate that the email field from the form is a valid email address
            try:
                validate_email(from_email)
            except ValidationError:
                raise ValidationError(
                    "The given email address is invalid. Please enter a valid email address."
                )

            # If the site does not have any contact emails or users, fallback to the default emails in AppJson
            if to_email_list is None or len(to_email_list) == 0:
                if AppJson.objects.filter(key="contact_us_default_emails").count() == 0:
                    logger.error(
                        'No emails found in the "contact_email" and "contact_users" fields found on site '
                        'and no default email set in AppJson model with key "contact_us_default_email".'
                    )
                    raise ContactUsError()
                else:
                    logger.warning(
                        f'No emails found in the contact_email and contact_users fields found on site "{site.title}".'
                    )

                    # Validate that the default emails are a list of strings
                    default_email = AppJson.objects.get(
                        key="contact_us_default_emails"
                    ).json
                    if not isinstance(default_email, list) or not all(
                        isinstance(email, str) for email in default_email
                    ):
                        logger.error(
                            'The "contact_us_default_emails" field in AppJson model must be a list of emails.'
                        )
                        raise ContactUsError()

                    to_email_list = default_email

            # If the site has excluded words, validate that the message does not contain any of them
            excluded_words = AppJson.objects.filter(key="contact_us_excluded_words")
            if excluded_words.count() > 0:
                word_list = excluded_words.first().json

                # Validate that the excluded words are a list of strings
                if not isinstance(word_list, list) or not all(
                    isinstance(word, str) for word in word_list
                ):
                    logger.error(
                        'The "contact_us_excluded_words" field in AppJson model must be a list of strings.'
                    )
                    raise ContactUsError()

                # Validate that the message does not contain any excluded words
                for word in word_list:
                    if re.search(word.lower(), (message + name + from_email).lower()):
                        logger.error(
                            f'Contact us message directed to site "{site.title}" contains excluded word. '
                            "The message will not be sent."
                        )
                        raise ValidationError(
                            "An excluded word has been found in the message. Please edit the "
                            "message and try again."
                        )

            try:
                # Format the final email
                final_message = (
                    "The following message was sent from the contact us form on the FirstVoices website:\n\n"
                    f"Name: {name}\n"
                    f"Email: {from_email}\n\n"
                    f"Message:\n{message}\n"
                )
                send_mail(
                    subject=f"Contact Us Form Submission from {name} ({from_email})",
                    message=final_message,
                    recipient_list=to_email_list,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                )
            except (ConnectionRefusedError, SMTPException) as e:
                logger.error(f"Contact us email failed to send. Error: {e}")
                raise ContactUsError()

            return Response(
                {"message": "The email has been successfully sent."}, status=202
            )
        except Exception as e:
            raise ContactUsError(e.message) if hasattr(
                e, "message"
            ) else ContactUsError()
