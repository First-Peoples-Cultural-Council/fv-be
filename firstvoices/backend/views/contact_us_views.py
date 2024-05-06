import logging
import re

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.models import AppJson, Site
from backend.serializers.contact_us_serializers import ContactUsSerializer
from backend.tasks.send_email_tasks import send_email_task
from backend.utils.contact_us_utils import get_fallback_emails
from backend.views import doc_strings
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin, ThrottlingMixin
from backend.views.doc_strings import error_403
from backend.views.exceptions import ContactUsError


@extend_schema_view(
    list=extend_schema(
        description="Returns the list of receiver emails used by the contact us post endpoint.",
        responses={
            200: ContactUsSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
        parameters=[site_slug_parameter],
    ),
    create=extend_schema(
        description="Sends emails to the addresses listed on the site contact_us_email and contact_us_users fields.",
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
    ThrottlingMixin,
    SiteContentViewSetMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    http_method_names = ["get", "post"]
    serializer_class = ContactUsSerializer
    pagination_class = None

    def get_queryset(self):
        site = self.get_validated_site()
        return Site.objects.filter(id=site.id)

    def list(self, request, *args, **kwargs):
        """
        Returns the list of receiver emails used by the contact-us post endpoint.
        """

        site = self.get_validated_site()

        # Using the Site model "change" permission here as only Language Admins and Super Admins should be able to
        # access the contact-us email list.
        perm = Site.get_perm("change")

        if not request.user.has_perm(perm, site):
            return Response({"message": error_403}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Sends emails to the addresses listed on the site contact_us_email and contact_us_users fields. A list of
        fallback email addresses can be set in the AppJson model with the key 'contact_us_default_emails'. If the
        site does not have any contact emails or users, the fallback email will be used. Additionally, the site can
        specify a list of excluded words in the AppJson model with the key 'contact_us_excluded_words'. If an email
        contains any of these words in the email, name, or message it will not be sent.
        """

        logger = logging.getLogger(__name__)
        site = self.get_validated_site()
        if request.user.is_anonymous:
            return Response(
                {"message": "You must be logged in to send an email."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            # Validate that all fields are present in the request
            if any(field not in request.data for field in ["name", "email", "message"]):
                raise ValidationError(
                    "Please fill out all fields before submitting the form."
                )
            name = request.data["name"]
            from_email = request.data["email"]
            message = request.data["message"]

            # Validate the input fields
            if not name or not from_email or not message:
                raise ValidationError(
                    "Please fill out all fields before submitting the form."
                )
            validate_email(from_email)

            # If the site has excluded words, validate that the message does not contain any of them
            self.validate_no_excluded_words(message, name, from_email, site)

            # Get the list of emails from the site contact emails and users fields
            to_email_list = site.contact_emails
            to_email_list.extend(site.contact_users.values_list("email", flat=True))

            # If the site does not have any contact emails or users, fallback to the default emails in AppJson
            if to_email_list is None or len(to_email_list) == 0:
                logger.warning(
                    f'No emails found in the contact_emails and contact_users fields found on site "{site.title}".'
                )
                to_email_list = get_fallback_emails()

            # Format the final email
            subject = f"Contact Us Form Submission from {name} ({from_email})"
            final_message = (
                "The following message was sent from the contact us form on the FirstVoices website:\n\n"
                f"Name: {name}\n"
                f"Email: {from_email}\n\n"
                f"Message:\n{message}\n"
            )

            send_email_task.apply_async((subject, final_message, to_email_list))

            return Response(
                {"message": "The email has been accepted."},
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            raise ContactUsError(e.message) if hasattr(
                e, "message"
            ) else ContactUsError()

    @staticmethod
    def validate_no_excluded_words(message, name, from_email, site):
        """
        Validates that the email, name, and message do not contain any excluded words. If the message contains any
        excluded words, an error is raised. The excluded words list can be set in the AppJson model with the key
        'contact_us_excluded_words'.
        """

        logger = logging.getLogger(__name__)
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
                raise ImproperlyConfigured()

            # Validate that the message does not contain any excluded words
            for word in word_list:
                if re.search(word.lower(), (message + name + from_email).lower()):
                    logger.info(
                        f'Contact us message directed to site "{site.title}" contains excluded word. '
                        "The message will not be sent."
                    )
                    raise ValidationError(
                        "An excluded word has been found in the message. Please edit the "
                        "message and try again."
                    )
